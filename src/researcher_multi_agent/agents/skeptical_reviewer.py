from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import SkepticalReviewerOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class SkepticalReviewer(DeterministicAgent[SkepticalReviewerOutput]):
    name = "SkepticalReviewer"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("skeptical_reviewer")

    @property
    def output_model(self) -> type[SkepticalReviewerOutput]:
        return SkepticalReviewerOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        has_topic = bool(state.topic_pool)
        if has_topic:
            return {
                "verdict": "PASS",
                "critical_issues": [],
                "minor_issues": ["Need literature grounding before supervisor outreach."],
                "unsupported_claims": [],
                "revision_instructions": ["Proceed to literature mapping in next milestone."],
                "confidence": "medium",
            }

        return {
            "verdict": "REVISE",
            "critical_issues": ["No candidate direction available for substantive review."],
            "minor_issues": [],
            "unsupported_claims": [],
            "revision_instructions": ["Run TopicStrategist first and resubmit."],
            "confidence": "high",
        }
