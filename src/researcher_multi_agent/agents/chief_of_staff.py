from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class ChiefOfStaff(DeterministicAgent[ChiefOfStaffOutput]):
    name = "ChiefOfStaff"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("chief_of_staff")

    @property
    def output_model(self) -> type[ChiefOfStaffOutput]:
        return ChiefOfStaffOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        has_topic = bool(state.topic_pool)
        delegations = []
        if not has_topic:
            delegations.append(
                {
                    "agent": "TopicStrategist",
                    "task": f"Narrow the goal into concrete directions: {task}",
                    "why_this_agent": "Goal is broad and needs precise research framing.",
                    "priority": "high",
                    "expected_output": "Scored candidate directions and recommended focus.",
                }
            )

        return {
            "goal_now": "Create a narrow research direction and quality-check it.",
            "assumptions": ["The user goal is still broad and exploratory."],
            "delegations": delegations,
            "merged_plan": {
                "now": ["Run TopicStrategist", "Run SkepticalReviewer"],
                "parallel": [],
                "later": ["Prepare literature mapping once topic is accepted"],
            },
            "risks": ["Topic may remain too vague without strict criteria."],
            "state_update": {
                "goal_profile": state.goal_profile.model_dump() if state.goal_profile else {},
            },
        }
