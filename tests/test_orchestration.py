from researcher_multi_agent.orchestrator.engine import OrchestrationEngine
from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput


def test_orchestration_runs_first_three_agents_path() -> None:
    engine = OrchestrationEngine()
    result = engine.run(goal="Find a strong first PhD project direction in oversight")

    assert result.chief_of_staff.goal_now
    assert result.topic_strategist is not None
    assert result.topic_strategist.recommended_focus
    assert result.skeptical_reviewer.verdict in {"PASS", "REVISE", "REJECT"}
    assert result.state.topic_pool
    assert result.state.review_log


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
    assert result.state.timeline[0]["event"] == "unhandled_delegation"
