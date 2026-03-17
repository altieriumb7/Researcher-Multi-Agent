from researcher_multi_agent.orchestrator.engine import OrchestrationEngine
from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput, SkepticalReviewerOutput


def test_orchestration_runs_milestone5_end_to_end_path() -> None:
    engine = OrchestrationEngine()
    result = engine.run(goal="Find a strong first PhD project direction in oversight")

    assert result.chief_of_staff.goal_now
    assert result.topic_strategist is not None
    assert result.literature_cartographer is not None
    assert result.project_architect is not None
    assert result.supervisor_mapper is not None
    assert result.narrative_writer is not None
    assert result.skeptical_reviewer.verdict in {"PASS", "REVISE", "REJECT"}
    assert result.state.topic_pool
    assert result.state.reading_board
    assert result.state.project_board
    assert result.state.target_supervisors
    assert result.state.drafts
    assert result.state.review_log

    executed = [item["agent"] for item in result.state.timeline if item["event"] == "delegation_executed"]
    assert executed == ["TopicStrategist", "LiteratureCartographer", "ProjectArchitect", "SupervisorMapper", "NarrativeWriter"]

    review_stages = [item["stage"] for item in result.state.review_log]
    assert review_stages == [
        "TopicStrategist",
        "LiteratureCartographer",
        "ProjectArchitect",
        "SupervisorMapper",
        "NarrativeWriter",
        "final",
    ]
    stage_verdicts = {item["stage"]: item["verdict"] for item in result.state.review_log}
    assert stage_verdicts["TopicStrategist"] == "PASS"
    assert stage_verdicts["LiteratureCartographer"] == "PASS"
    assert stage_verdicts["ProjectArchitect"] == "PASS"
    assert stage_verdicts["SupervisorMapper"] == "PASS"
    assert stage_verdicts["NarrativeWriter"] == "PASS"

    assert result.state.state_snapshots[0]["stage"] == "initialized"
    assert result.state.state_snapshots[-1]["stage"] == "final"


def test_orchestration_records_unhandled_delegations() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "UnknownAgent",
                        "task": "mystery",
                        "why_this_agent": "",
                        "priority": "high",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.topic_strategist is None
    assert result.literature_cartographer is None
    assert result.project_architect is None
    assert result.supervisor_mapper is None
    assert result.narrative_writer is None
    assert any(item["event"] == "unhandled_delegation" for item in result.state.timeline)


def test_review_gate_blocks_following_stages_when_rejected() -> None:
    engine = OrchestrationEngine()

    def fake_reviewer_run(task: str, state):
        if task.startswith("Review gate for TopicStrategist"):
            return SkepticalReviewerOutput.model_validate(
                {
                    "verdict": "REJECT",
                    "critical_issues": ["Invalid topic framing"],
                    "minor_issues": [],
                    "unsupported_claims": [],
                    "revision_instructions": ["Re-run topic stage"],
                    "confidence": "high",
                }
            )
        return SkepticalReviewerOutput.model_validate(
            {
                "verdict": "PASS",
                "critical_issues": [],
                "minor_issues": [],
                "unsupported_claims": [],
                "revision_instructions": [],
                "confidence": "medium",
            }
        )

    engine.reviewer.run = fake_reviewer_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.topic_strategist is not None
    assert result.literature_cartographer is None
    assert result.project_architect is None
    assert result.supervisor_mapper is None
    assert result.narrative_writer is None

    blocked_events = [item for item in result.state.timeline if item["event"] == "delegation_blocked_by_review_gate"]
    assert blocked_events
    assert {event["agent"] for event in blocked_events} == {
        "LiteratureCartographer",
        "ProjectArchitect",
        "SupervisorMapper",
        "NarrativeWriter",
    }


def test_milestone3_skips_project_when_literature_missing() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "ProjectArchitect",
                        "task": "Design project",
                        "why_this_agent": "",
                        "priority": "high",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.project_architect is None
    assert not result.state.project_board
    skip_event = next(item for item in result.state.timeline if item["event"] == "delegation_skipped_missing_dependency")
    assert skip_event["requires"] == "reading_board"


def test_milestone3_skips_literature_when_topic_missing() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "LiteratureCartographer",
                        "task": "Map literature",
                        "why_this_agent": "",
                        "priority": "high",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.literature_cartographer is None
    assert not result.state.reading_board
    skip_event = next(item for item in result.state.timeline if item["event"] == "delegation_skipped_missing_dependency")
    assert skip_event["requires"] == "topic_pool"


def test_milestone4_skips_supervisor_mapper_when_project_missing() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "SupervisorMapper",
                        "task": "Rank supervisors",
                        "why_this_agent": "",
                        "priority": "high",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.supervisor_mapper is None
    assert not result.state.target_supervisors
    skip_event = next(item for item in result.state.timeline if item["event"] == "delegation_skipped_missing_dependency")
    assert skip_event["requires"] == "project_board"


def test_milestone4_skips_narrative_writer_when_targets_missing() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        state.project_board = [{"project_title": "seed"}]
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "NarrativeWriter",
                        "task": "Draft outreach",
                        "why_this_agent": "",
                        "priority": "high",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.narrative_writer is None
    assert not result.state.drafts
    skip_event = next(item for item in result.state.timeline if item["event"] == "delegation_skipped_missing_dependency")
    assert skip_event["requires"] == "target_supervisors"


def test_milestone4_skips_narrative_writer_when_project_missing() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "NarrativeWriter",
                        "task": "Draft outreach",
                        "why_this_agent": "",
                        "priority": "high",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.narrative_writer is None
    assert not result.state.drafts
    skip_event = next(item for item in result.state.timeline if item["event"] == "delegation_skipped_missing_dependency")
    assert skip_event["requires"] == "project_board"


def test_orchestration_emits_trace_hook_events() -> None:
    traced_events: list[dict] = []
    engine = OrchestrationEngine(trace_hook=traced_events.append)

    _ = engine.run(goal="Find a strong first PhD project direction in oversight")

    assert traced_events
    assert any(event["event"] == "chief_plan_created" for event in traced_events)
    assert any(event["event"] == "state_snapshot" for event in traced_events)
    assert any(event["event"] == "final_review_completed" for event in traced_events)


def test_orchestration_applies_chief_goal_profile_state_update() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {
                    "goal_profile": {
                        "user_goal": "updated goal",
                        "constraints": ["time-boxed", "low compute"],
                    }
                },
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="original goal")

    assert result.state.goal_profile is not None
    assert result.state.goal_profile.user_goal == "updated goal"
    assert result.state.goal_profile.constraints == ["time-boxed", "low compute"]



def test_orchestration_applies_chief_list_state_updates() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {
                    "topic_pool": [{"seed": "topic"}],
                    "timeline": [{"event": "seeded_by_chief"}],
                },
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="original goal")

    assert result.state.topic_pool == [{"seed": "topic"}]
    assert result.state.timeline == [{"event": "seeded_by_chief"}, {"event": "final_review_completed", "verdict": result.skeptical_reviewer.verdict}]



def test_orchestration_records_specialist_failure_and_blocks_following() -> None:
    engine = OrchestrationEngine()

    def failing_topic_run(task: str, state):
        raise RuntimeError("synthetic topic failure")

    engine.topic.run = failing_topic_run  # type: ignore[method-assign]

    result = engine.run(goal="test specialist failure")

    failure_events = [item for item in result.state.timeline if item["event"] == "delegation_failed"]
    assert len(failure_events) == 1
    assert failure_events[0]["agent"] == "TopicStrategist"
    assert "RuntimeError: synthetic topic failure" in failure_events[0]["error"]

    blocked_events = [item for item in result.state.timeline if item["event"] == "delegation_blocked_by_review_gate"]
    assert blocked_events
    assert {event["agent"] for event in blocked_events} == {
        "LiteratureCartographer",
        "ProjectArchitect",
        "SupervisorMapper",
        "NarrativeWriter",
    }

    assert result.skeptical_reviewer is not None
    assert result.state.review_log[-1]["stage"] == "final"


def test_orchestration_truncates_excessive_delegations() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        delegations = [
            {
                "agent": "UnknownAgent",
                "task": f"task-{index}",
                "why_this_agent": "",
                "priority": "high",
                "expected_output": "",
            }
            for index in range(15)
        ]
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": delegations,
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    truncation_events = [item for item in result.state.timeline if item["event"] == "delegations_truncated"]
    assert len(truncation_events) == 1
    assert truncation_events[0]["max_allowed"] == 12
    assert truncation_events[0]["dropped_count"] == 3

    unhandled_events = [item for item in result.state.timeline if item["event"] == "unhandled_delegation"]
    assert len(unhandled_events) == 12


def test_orchestration_rejects_non_dict_chief_list_updates() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {
                    "topic_pool": [{"seed": "ok"}],
                    "timeline": ["bad-event", {"event": "good-event"}],
                },
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]
    result = engine.run(goal="test")

    assert result.state.topic_pool == [{"seed": "ok"}]
    assert result.state.timeline
    rejection_events = [item for item in result.state.timeline if item["event"] == "chief_state_update_rejected"]
    assert len(rejection_events) == 1
    assert rejection_events[0]["field"] == "timeline"
    assert rejection_events[0]["reason"] == "expected_list_of_dict"


def test_orchestration_routes_goal_mode_into_chief_task() -> None:
    engine = OrchestrationEngine()
    captured_task: dict[str, str] = {}

    def fake_chief_run(task: str, state):
        captured_task["task"] = task
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]

    result = engine.run(goal="Which company and universities are treating this topic as hot topics?")

    assert result.goal_intent.mode == "MAP"
    assert "Mode: MAP" in captured_task["task"]
    assert "Deliverables contract must_include" in captured_task["task"]
    assert any(item["event"] == "goal_interpreted" for item in result.state.timeline)
