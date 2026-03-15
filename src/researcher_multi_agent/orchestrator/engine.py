from __future__ import annotations

from dataclasses import dataclass

from researcher_multi_agent.agents.chief_of_staff import ChiefOfStaff
from researcher_multi_agent.agents.skeptical_reviewer import SkepticalReviewer
from researcher_multi_agent.agents.topic_strategist import TopicStrategist
from researcher_multi_agent.orchestrator.routing import route_delegations
from researcher_multi_agent.schemas.agent_outputs import (
    ChiefOfStaffOutput,
    SkepticalReviewerOutput,
    TopicStrategistOutput,
)
from researcher_multi_agent.schemas.state import GoalProfile, SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


@dataclass
class OrchestrationResult:
    chief_of_staff: ChiefOfStaffOutput
    topic_strategist: TopicStrategistOutput | None
    skeptical_reviewer: SkepticalReviewerOutput
    state: SharedState


class OrchestrationEngine:
    def __init__(self, prompt_loader: PromptLoader | None = None) -> None:
        loader = prompt_loader or PromptLoader()
        self.chief = ChiefOfStaff(loader)
        self.topic = TopicStrategist(loader)
        self.reviewer = SkepticalReviewer(loader)

    def _dispatch_delegation(self, state: SharedState, agent_name: str, task: str) -> TopicStrategistOutput | None:
        if agent_name == "TopicStrategist":
            topic_result = self.topic.run(task=task, state=state)
            state.topic_pool = [topic_result.model_dump()]
            return topic_result

        state.timeline.append(
            {
                "event": "unhandled_delegation",
                "agent": agent_name,
                "task": task,
            }
        )
        return None

    def run(self, goal: str, constraints: list[str] | None = None) -> OrchestrationResult:
        state = SharedState(goal_profile=GoalProfile(user_goal=goal, constraints=constraints or []))

        chief_result = self.chief.run(task=goal, state=state)
        routes = route_delegations(chief_result)

        topic_result: TopicStrategistOutput | None = None
        for agent_name, task in routes:
            delegated_result = self._dispatch_delegation(state=state, agent_name=agent_name, task=task)
            if delegated_result is not None:
                topic_result = delegated_result

        reviewer_result = self.reviewer.run(task="Review the latest topic recommendation.", state=state)
        state.review_log.append(reviewer_result.model_dump())

        return OrchestrationResult(
            chief_of_staff=chief_result,
            topic_strategist=topic_result,
            skeptical_reviewer=reviewer_result,
            state=state,
        )
