from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import NarrativeWriterOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class NarrativeWriter(DeterministicAgent[NarrativeWriterOutput]):
    name = "NarrativeWriter"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("narrative_writer")

    @property
    def output_model(self) -> type[NarrativeWriterOutput]:
        return NarrativeWriterOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        primary_target = "Supervisor"
        institution = "target lab"
        if state.target_supervisors:
            primary = state.target_supervisors[0].get("targets", [{}])[0]
            primary_target = primary.get("name", primary_target)
            institution = primary.get("institution", institution)

        return {
            "document_type": "supervisor_outreach_email",
            "target_audience": f"{primary_target} at {institution}",
            "tone": "concise, rigorous, collegial",
            "drafts": [
                {
                    "version_name": "direct_fit_intro",
                    "text": (
                        f"Dear Prof. {primary_target},\n\n"
                        "I am preparing a first PhD project on low-compute probes for predicting reasoning failures in LLM traces. "
                        "Your group’s work on reliable reasoning evaluation overlaps directly with the methodology I plan to test. "
                        "I would value your feedback on a scoped experiment comparing probe-based risk prediction against entropy and self-consistency baselines on GSM8K/MATH under fixed compute budgets.\n\n"
                        "If this direction is relevant to your current priorities, I would be grateful for a short discussion on fit and potential supervision pathways.\n\n"
                        "Best regards,\n"
                        "[Your Name]"
                    ),
                }
            ],
            "customization_slots": [
                "Insert one specific recent paper/theme from the target lab",
                "Insert one sentence linking your prior experience to the proposed method",
                "Insert country/funding/logistics line if relevant",
            ],
            "weak_sentences_to_avoid": [
                "I am passionate about AI.",
                "Your research inspires me greatly.",
                "My profile perfectly matches your lab.",
            ],
        }
