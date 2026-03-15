from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from researcher_multi_agent.agents.chief_of_staff import ChiefOfStaff
from researcher_multi_agent.agents.literature_cartographer import LiteratureCartographer
from researcher_multi_agent.agents.project_architect import ProjectArchitect
from researcher_multi_agent.agents.skeptical_reviewer import SkepticalReviewer
from researcher_multi_agent.agents.topic_strategist import TopicStrategist
from researcher_multi_agent.orchestrator.routing import route_delegations
from researcher_multi_agent.schemas.agent_outputs import (
    ChiefOfStaffOutput,
    LiteratureCartographerOutput,
    ProjectArchitectOutput,
    SkepticalReviewerOutput,
    TopicStrategistOutput,
)
from researcher_multi_agent.schemas.state import GoalProfile, SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


@dataclass
class OrchestrationResult:
    chief_of_staff: ChiefOfStaffOutput
    topic_strategist: TopicStrategistOutput | None
    literature_cartographer: LiteratureCartographerOutput | None
    project_architect: ProjectArchitectOutput | None
    skeptical_reviewer: SkepticalReviewerOutput
    state: SharedState


class OrchestrationEngine:
    def __init__(self, prompt_loader: PromptLoader | None = None) -> None:
        loader = prompt_loader or PromptLoader()
        self.chief = ChiefOfStaff(loader)
        self.topic = TopicStrategist(loader)
        self.literature = LiteratureCartographer(loader)
        self.project = ProjectArchitect(loader)
        self.reviewer = SkepticalReviewer(loader)

    def run(self, goal: str, constraints: list[str] | None = None) -> OrchestrationResult:
        state = SharedState(goal_profile=GoalProfile(user_goal=goal, constraints=constraints or []))

        chief_result = self.chief.run(task=goal, state=state)
        routes = route_delegations(chief_result)

        topic_result: TopicStrategistOutput | None = None
        literature_result: LiteratureCartographerOutput | None = None
        project_result: ProjectArchitectOutput | None = None

        def run_topic(task: str) -> bool:
            nonlocal topic_result
            topic_result = self.topic.run(task=task, state=state)
            state.topic_pool = [topic_result.model_dump()]
            return True

        def run_literature(task: str) -> bool:
            nonlocal literature_result
            if not state.topic_pool:
                state.timeline.append(
                    {
                        "event": "delegation_skipped_missing_dependency",
                        "agent": "LiteratureCartographer",
                        "task": task,
                        "requires": "topic_pool",
                    }
                )
                return False
            literature_result = self.literature.run(task=task, state=state)
            state.reading_board = [literature_result.model_dump()]
            return True

        def run_project(task: str) -> bool:
            nonlocal project_result
            if not state.reading_board:
                state.timeline.append(
                    {
                        "event": "delegation_skipped_missing_dependency",
                        "agent": "ProjectArchitect",
                        "task": task,
                        "requires": "reading_board",
                    }
                )
                return False
            project_result = self.project.run(task=task, state=state)
            state.project_board = [project_result.model_dump()]
            return True

        specialist_router: dict[str, Callable[[str], bool]] = {
            "TopicStrategist": run_topic,
            "LiteratureCartographer": run_literature,
            "ProjectArchitect": run_project,
            # Milestone 4 agents can be added here without changing control flow.
        }

        for agent_name, task in routes:
            handler = specialist_router.get(agent_name)
            if handler:
                was_executed = handler(task)
                if was_executed:
                    state.timeline.append(
                        {
                            "event": "delegation_executed",
                            "agent": agent_name,
                            "task": task,
                        }
                    )
            else:
                state.timeline.append(
                    {
                        "event": "unhandled_delegation",
                        "agent": agent_name,
                        "task": task,
                    }
                )

        reviewer_result = self.reviewer.run(task="Review the latest planning artifacts.", state=state)
        state.review_log.append(reviewer_result.model_dump())

        return OrchestrationResult(
            chief_of_staff=chief_result,
            topic_strategist=topic_result,
            literature_cartographer=literature_result,
            project_architect=project_result,
            skeptical_reviewer=reviewer_result,
            state=state,
        )
