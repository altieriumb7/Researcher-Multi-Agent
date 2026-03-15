from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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

    def run(self, goal: str, constraints: list[str] | None = None) -> OrchestrationResult:
        state = SharedState(goal_profile=GoalProfile(user_goal=goal, constraints=constraints or []))

        chief_result = self.chief.run(task=goal, state=state)
        routes = route_delegations(chief_result)

        topic_result: TopicStrategistOutput | None = None

        def run_topic(task: str) -> None:
            nonlocal topic_result
            topic_result = self.topic.run(task=task, state=state)
            state.topic_pool = [topic_result.model_dump()]

        specialist_router: dict[str, Callable[[str], None]] = {
            "TopicStrategist": run_topic,
            # Milestones 3-4 agents can be added here without changing control flow.
        }

        for agent_name, task in routes:
            handler = specialist_router.get(agent_name)
            if handler:
                handler(task)
            else:
                state.timeline.append(
                    {
                        "event": "unhandled_delegation",
                        "agent": agent_name,
                        "task": task,
                    }
                )

        reviewer_result = self.reviewer.run(task="Review the latest topic recommendation.", state=state)
        state.review_log.append(reviewer_result.model_dump())

        return OrchestrationResult(
            chief_of_staff=chief_result,
            topic_strategist=topic_result,
            skeptical_reviewer=reviewer_result,
            state=state,
        )
