from researcher_multi_agent.orchestrator.routing import route_delegations
from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput


def test_route_delegations_orders_by_priority() -> None:
    plan = ChiefOfStaffOutput.model_validate(
        {
            "goal_now": "goal",
            "assumptions": [],
            "delegations": [
                {
                    "agent": "AgentLow",
                    "task": "low task",
                    "why_this_agent": "",
                    "priority": "low",
                    "expected_output": "",
                },
                {
                    "agent": "AgentHigh",
                    "task": "high task",
                    "why_this_agent": "",
                    "priority": "high",
                    "expected_output": "",
                },
            ],
            "merged_plan": {"now": [], "parallel": [], "later": []},
            "risks": [],
            "state_update": {},
        }
    )

    routes = route_delegations(plan)
    assert routes == [("AgentHigh", "high task"), ("AgentLow", "low task")]
