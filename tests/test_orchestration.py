from researcher_multi_agent.orchestrator.engine import OrchestrationEngine
from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput


def test_orchestration_runs_milestone3_path() -> None:
    engine = OrchestrationEngine()
    result = engine.run(goal="Find a strong first PhD project direction in oversight")

    assert result.chief_of_staff.goal_now
    assert result.topic_strategist is not None
    assert result.literature_cartographer is not None
    assert result.project_architect is not None
    assert result.skeptical_reviewer.verdict in {"PASS", "REVISE", "REJECT"}
    assert result.state.topic_pool
    assert result.state.reading_board
    assert result.state.project_board
    assert result.state.review_log

    executed = [item["agent"] for item in result.state.timeline if item["event"] == "delegation_executed"]
    assert executed == ["TopicStrategist", "LiteratureCartographer", "ProjectArchitect"]


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
    assert result.state.timeline[0]["event"] == "unhandled_delegation"


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
    assert result.state.timeline[0]["event"] == "delegation_skipped_missing_dependency"
    assert result.state.timeline[0]["requires"] == "reading_board"


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
    assert result.state.timeline[0]["event"] == "delegation_skipped_missing_dependency"
    assert result.state.timeline[0]["requires"] == "topic_pool"
