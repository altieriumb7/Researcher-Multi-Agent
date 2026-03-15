from __future__ import annotations

from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput


def route_delegations(plan: ChiefOfStaffOutput) -> list[tuple[str, str]]:
    """Return ordered (agent_name, task) pairs from ChiefOfStaff delegations."""
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    ordered = sorted(plan.delegations, key=lambda delegation: priority_rank[delegation.priority])
    return [(delegation.agent, delegation.task) for delegation in ordered]
