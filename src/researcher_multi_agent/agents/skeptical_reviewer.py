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
        stage_requirements = {
            "TopicStrategist": ("topic_pool", "candidate directions from TopicStrategist"),
            "LiteratureCartographer": ("reading_board", "literature map from LiteratureCartographer"),
            "ProjectArchitect": ("project_board", "project design from ProjectArchitect"),
            "SupervisorMapper": ("target_supervisors", "supervisor targeting from SupervisorMapper"),
            "NarrativeWriter": ("drafts", "outreach draft from NarrativeWriter"),
        }

        for stage, (field_name, label) in stage_requirements.items():
            if f"Review gate for {stage}" in task:
                if getattr(state, field_name):
                    return {
                        "verdict": "PASS",
                        "critical_issues": [],
                        "minor_issues": [],
                        "unsupported_claims": [],
                        "revision_instructions": [],
                        "confidence": "medium",
                    }
                return {
                    "verdict": "REVISE",
                    "critical_issues": [f"Missing required artifact: {label}."],
                    "minor_issues": [],
                    "unsupported_claims": [],
                    "revision_instructions": [f"Run {stage} and resubmit for review."],
                    "confidence": "high",
                }

        if state.drafts:
            return {
                "verdict": "PASS",
                "critical_issues": [],
                "minor_issues": ["Next step: tailor final draft per supervisor profile."],
                "unsupported_claims": [],
                "revision_instructions": ["Proceed with customization and sending strategy."],
                "confidence": "medium",
            }

        if state.topic_pool:
            return {
                "verdict": "REVISE",
                "critical_issues": ["Planning pipeline incomplete: no outreach draft available."],
                "minor_issues": [],
                "unsupported_claims": [],
                "revision_instructions": ["Complete remaining stages before final review."],
                "confidence": "high",
            }

        return {
            "verdict": "REVISE",
            "critical_issues": ["No candidate direction available for substantive review."],
            "minor_issues": [],
            "unsupported_claims": [],
            "revision_instructions": ["Run TopicStrategist first and resubmit."],
            "confidence": "high",
        }
