from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from researcher_multi_agent.agents.chief_of_staff import ChiefOfStaff
from researcher_multi_agent.agents.goal_interpreter import GoalInterpreter
from researcher_multi_agent.agents.literature_cartographer import LiteratureCartographer
from researcher_multi_agent.agents.project_architect import ProjectArchitect
from researcher_multi_agent.agents.narrative_writer import NarrativeWriter
from researcher_multi_agent.agents.skeptical_reviewer import SkepticalReviewer
from researcher_multi_agent.agents.supervisor_mapper import SupervisorMapper
from researcher_multi_agent.agents.topic_strategist import TopicStrategist
from researcher_multi_agent.orchestrator.routing import route_delegations
from researcher_multi_agent.schemas.agent_outputs import (
    ChiefOfStaffOutput,
    GoalDeliverables,
    GoalIntentOutput,
    LiteratureCartographerOutput,
    ProjectArchitectOutput,
    NarrativeWriterOutput,
    SkepticalReviewerOutput,
    SupervisorMapperOutput,
    TopicStrategistOutput,
)
from researcher_multi_agent.schemas.state import GoalProfile, SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)
MAX_DELEGATIONS_PER_RUN = 12
MAX_STAGE_ATTEMPTS = 2


@dataclass
class OrchestrationResult:
    goal_intent: GoalIntentOutput
    chief_of_staff: ChiefOfStaffOutput
    topic_strategist: TopicStrategistOutput | None
    literature_cartographer: LiteratureCartographerOutput | None
    project_architect: ProjectArchitectOutput | None
    supervisor_mapper: SupervisorMapperOutput | None
    narrative_writer: NarrativeWriterOutput | None
    skeptical_reviewer: SkepticalReviewerOutput
    state: SharedState


class OrchestrationEngine:
    def __init__(
        self,
        prompt_loader: PromptLoader | None = None,
        trace_hook: Callable[[dict], None] | None = None,
    ) -> None:
        loader = prompt_loader or PromptLoader()
        self.goal_interpreter = GoalInterpreter()
        self.chief = ChiefOfStaff(loader)
        self.topic = TopicStrategist(loader)
        self.literature = LiteratureCartographer(loader)
        self.project = ProjectArchitect(loader)
        self.supervisor_mapper = SupervisorMapper(loader)
        self.narrative_writer = NarrativeWriter(loader)
        self.reviewer = SkepticalReviewer(loader)
        self.trace_hook = trace_hook

    def _emit_trace(self, event: dict) -> None:
        logger.info("orchestration_event", extra={"event_payload": event})
        if self.trace_hook is not None:
            self.trace_hook(event)

    def _snapshot_state(self, state: SharedState, stage: str) -> None:
        snapshot = {
            "stage": stage,
            "topic_pool": len(state.topic_pool),
            "reading_board": len(state.reading_board),
            "project_board": len(state.project_board),
            "target_supervisors": len(state.target_supervisors),
            "drafts": len(state.drafts),
            "review_log": len(state.review_log),
            "timeline": len(state.timeline),
        }
        state.state_snapshots.append(snapshot)
        self._emit_trace({"event": "state_snapshot", **snapshot})

    def _run_review_gate(
        self,
        state: SharedState,
        stage: str,
        contract: GoalDeliverables,
        mode: str,
    ) -> SkepticalReviewerOutput:
        review = self.reviewer.review(stage=stage, state=state, contract=contract, mode=mode)
        review_payload = review.model_dump()
        review_payload["stage"] = stage
        state.review_log.append(review_payload)

        gate_event = {
            "event": "review_gate",
            "stage": stage,
            "verdict": review.verdict,
        }
        state.timeline.append(gate_event)
        self._emit_trace(gate_event)

        return review

    def _apply_chief_state_update(self, state: SharedState, chief_result: ChiefOfStaffOutput) -> None:
        state_update = chief_result.state_update

        def _coerce_dict_list(key: str, value: object) -> list[dict] | None:
            if not isinstance(value, list):
                return None
            if all(isinstance(item, dict) for item in value):
                return value
            dropped_event = {
                "event": "chief_state_update_rejected",
                "field": key,
                "reason": "expected_list_of_dict",
            }
            state.timeline.append(dropped_event)
            self._emit_trace(dropped_event)
            return None

        goal_profile_update = state_update.get("goal_profile")
        if isinstance(goal_profile_update, dict) and goal_profile_update.get("user_goal"):
            state.goal_profile = GoalProfile(
                user_goal=goal_profile_update["user_goal"],
                constraints=list(goal_profile_update.get("constraints", [])),
            )

        for key in [
            "topic_pool",
            "reading_board",
            "project_board",
            "target_supervisors",
            "drafts",
            "review_log",
            "timeline",
        ]:
            value = _coerce_dict_list(key=key, value=state_update.get(key))
            if value is not None:
                setattr(state, key, value)

    def run(self, goal: str, constraints: list[str] | None = None) -> OrchestrationResult:
        state = SharedState(goal_profile=GoalProfile(user_goal=goal, constraints=constraints or []))
        self._snapshot_state(state, stage="initialized")

        goal_intent = self.goal_interpreter.run(task=goal, state=state)
        state.timeline.append({"event": "goal_interpreted", **goal_intent.model_dump()})
        self._emit_trace({"event": "goal_interpreted", "mode": goal_intent.mode})

        state.goal_profile.constraints = [
            *state.goal_profile.constraints,
            f"mode={goal_intent.mode}",
            f"must_include={'; '.join(goal_intent.deliverables.must_include)}",
            f"nice_to_have={'; '.join(goal_intent.deliverables.nice_to_have)}",
            f"success_criteria={'; '.join(goal_intent.success_criteria)}",
        ]

        planning_task = (
            f"Goal: {goal}\n"
            f"Mode: {goal_intent.mode}\n"
            f"Deliverables contract must_include: {goal_intent.deliverables.must_include}\n"
            f"Deliverables contract nice_to_have: {goal_intent.deliverables.nice_to_have}\n"
            f"Success criteria: {goal_intent.success_criteria}\n"
            f"Assumptions: {goal_intent.assumptions}"
        )
        chief_result = self.chief.run(task=planning_task, state=state)
        self._apply_chief_state_update(state=state, chief_result=chief_result)
        routes = route_delegations(chief_result)
        if len(routes) > MAX_DELEGATIONS_PER_RUN:
            truncation_event = {
                "event": "delegations_truncated",
                "max_allowed": MAX_DELEGATIONS_PER_RUN,
                "dropped_count": len(routes) - MAX_DELEGATIONS_PER_RUN,
            }
            state.timeline.append(truncation_event)
            self._emit_trace(truncation_event)
            routes = routes[:MAX_DELEGATIONS_PER_RUN]
        self._emit_trace({"event": "chief_plan_created", "delegations": len(routes)})

        topic_result: TopicStrategistOutput | None = None
        literature_result: LiteratureCartographerOutput | None = None
        project_result: ProjectArchitectOutput | None = None
        supervisor_result: SupervisorMapperOutput | None = None
        narrative_result: NarrativeWriterOutput | None = None

        def run_topic(task: str) -> bool:
            nonlocal topic_result
            topic_result = self.topic.run(task=task, state=state)
            state.topic_pool = [topic_result.model_dump()]
            return True

        def run_literature(task: str) -> bool:
            nonlocal literature_result
            if not state.topic_pool:
                skip_event = {
                    "event": "delegation_skipped_missing_dependency",
                    "agent": "LiteratureCartographer",
                    "task": task,
                    "requires": "topic_pool",
                }
                state.timeline.append(skip_event)
                self._emit_trace(skip_event)
                return False
            literature_result = self.literature.run(task=task, state=state)
            state.reading_board = [literature_result.model_dump()]
            return True

        def run_project(task: str) -> bool:
            nonlocal project_result
            if not state.reading_board:
                skip_event = {
                    "event": "delegation_skipped_missing_dependency",
                    "agent": "ProjectArchitect",
                    "task": task,
                    "requires": "reading_board",
                }
                state.timeline.append(skip_event)
                self._emit_trace(skip_event)
                return False
            project_result = self.project.run(task=task, state=state)
            state.project_board = [project_result.model_dump()]
            return True

        def run_supervisor_mapper(task: str) -> bool:
            nonlocal supervisor_result
            if not state.project_board:
                skip_event = {
                    "event": "delegation_skipped_missing_dependency",
                    "agent": "SupervisorMapper",
                    "task": task,
                    "requires": "project_board",
                }
                state.timeline.append(skip_event)
                self._emit_trace(skip_event)
                return False
            supervisor_result = self.supervisor_mapper.run(task=task, state=state)
            state.target_supervisors = [supervisor_result.model_dump()]
            return True

        def run_narrative_writer(task: str) -> bool:
            nonlocal narrative_result
            if not state.project_board:
                skip_event = {
                    "event": "delegation_skipped_missing_dependency",
                    "agent": "NarrativeWriter",
                    "task": task,
                    "requires": "project_board",
                }
                state.timeline.append(skip_event)
                self._emit_trace(skip_event)
                return False
            if not state.target_supervisors:
                skip_event = {
                    "event": "delegation_skipped_missing_dependency",
                    "agent": "NarrativeWriter",
                    "task": task,
                    "requires": "target_supervisors",
                }
                state.timeline.append(skip_event)
                self._emit_trace(skip_event)
                return False
            narrative_result = self.narrative_writer.run(task=task, state=state)
            state.drafts = [narrative_result.model_dump()]
            return True

        specialist_router: dict[str, Callable[[str], bool]] = {
            "TopicStrategist": run_topic,
            "LiteratureCartographer": run_literature,
            "ProjectArchitect": run_project,
            "SupervisorMapper": run_supervisor_mapper,
            "NarrativeWriter": run_narrative_writer,
        }

        delegation_attempts = 0
        route_index = 0
        while route_index < len(routes) and delegation_attempts < MAX_DELEGATIONS_PER_RUN:
            agent_name, task = routes[route_index]
            route_index += 1
            delegation_attempts += 1

            handler = specialist_router.get(agent_name)
            if handler is None:
                unhandled_event = {
                    "event": "unhandled_delegation",
                    "agent": agent_name,
                    "task": task,
                }
                state.timeline.append(unhandled_event)
                self._emit_trace(unhandled_event)
                self._snapshot_state(state, stage=f"unhandled_{agent_name}")
                continue

            attempts = 0
            while attempts < MAX_STAGE_ATTEMPTS:
                try:
                    was_executed = handler(task)
                except Exception as exc:
                    failure_event = {
                        "event": "delegation_failed",
                        "agent": agent_name,
                        "task": task,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                    state.timeline.append(failure_event)
                    self._emit_trace(failure_event)
                    self._snapshot_state(state, stage=f"failed_{agent_name}")
                    break

                if not was_executed:
                    self._snapshot_state(state, stage=f"skipped_{agent_name}")
                    break

                executed_event = {
                    "event": "delegation_executed",
                    "agent": agent_name,
                    "task": task,
                    "attempt": attempts + 1,
                }
                state.timeline.append(executed_event)
                self._emit_trace(executed_event)

                review = self._run_review_gate(
                    state=state,
                    stage=agent_name,
                    contract=goal_intent.deliverables,
                    mode=goal_intent.mode,
                )
                self._snapshot_state(state, stage=agent_name)

                if review.verdict == "PASS":
                    break

                if review.verdict == "REVISE":
                    attempts += 1
                    revision_task = " ".join(review.revision_instructions) if review.revision_instructions else "Address reviewer issues."
                    task = f"REVISION REQUIRED. Apply: {revision_task}. Original task: {task}"
                    revise_event = {
                        "event": "delegation_revision_requested",
                        "agent": agent_name,
                        "attempt": attempts,
                    }
                    state.timeline.append(revise_event)
                    self._emit_trace(revise_event)
                    continue

                if review.verdict == "REJECT":
                    reject_event = {
                        "event": "review_gate_rejected",
                        "stage": agent_name,
                    }
                    state.timeline.append(reject_event)
                    self._emit_trace(reject_event)
                    chief_result = self.chief.run(task=planning_task, state=state)
                    self._apply_chief_state_update(state=state, chief_result=chief_result)
                    routes = route_delegations(chief_result)
                    if len(routes) > MAX_DELEGATIONS_PER_RUN:
                        routes = routes[:MAX_DELEGATIONS_PER_RUN]
                    route_index = 0
                    replanned_event = {
                        "event": "delegations_replanned",
                        "delegations": len(routes),
                    }
                    state.timeline.append(replanned_event)
                    self._emit_trace(replanned_event)
                    break

            if attempts >= MAX_STAGE_ATTEMPTS:
                exhausted_event = {
                    "event": "stage_attempts_exhausted",
                    "agent": agent_name,
                    "max_attempts": MAX_STAGE_ATTEMPTS,
                }
                state.timeline.append(exhausted_event)
                self._emit_trace(exhausted_event)

        reviewer_result = self.reviewer.review(stage="final", state=state, contract=goal_intent.deliverables, mode=goal_intent.mode)
        final_review = reviewer_result.model_dump()
        final_review["stage"] = "final"
        state.review_log.append(final_review)
        final_event = {
            "event": "final_review_completed",
            "verdict": reviewer_result.verdict,
        }
        state.timeline.append(final_event)
        self._emit_trace(final_event)
        self._snapshot_state(state, stage="final")

        return OrchestrationResult(
            goal_intent=goal_intent,
            chief_of_staff=chief_result,
            topic_strategist=topic_result,
            literature_cartographer=literature_result,
            project_architect=project_result,
            supervisor_mapper=supervisor_result,
            narrative_writer=narrative_result,
            skeptical_reviewer=reviewer_result,
            state=state,
        )
