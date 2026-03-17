import json

from researcher_multi_agent.agents.llm_base import LLMAgent
from typing import Any
from researcher_multi_agent.schemas.agent_outputs import NarrativeWriterOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class NarrativeWriter(LLMAgent[NarrativeWriterOutput]):
    name = "NarrativeWriter"

    def __init__(self, prompt_loader: PromptLoader, llm_client: Any | None = None) -> None:
        self._fallback_mode = llm_client is None
        if llm_client is None:
            self.prompt = prompt_loader.load("narrative_writer")
            self.llm_client = None
            return
        super().__init__(llm_client=llm_client, prompt=prompt_loader.load("narrative_writer"))

    @property
    def output_model(self) -> type[NarrativeWriterOutput]:
        return NarrativeWriterOutput

    @property
    def output_schema(self) -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["document_type", "target_audience", "tone", "drafts", "customization_slots", "weak_sentences_to_avoid", "evidence"],
            "properties": {
                "document_type": {"type": "string"},
                "target_audience": {"type": "string"},
                "tone": {"type": "string"},
                "drafts": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["version_name", "text"], "properties": {"version_name": {"type": "string"}, "text": {"type": "string"}}}},
                "customization_slots": {"type": "array", "items": {"type": "string"}},
                "weak_sentences_to_avoid": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["claim", "source", "confidence"], "properties": {"claim": {"type": "string"}, "source": {"type": "string"}, "confidence": {"type": "string", "enum": ["low", "medium", "high"]}}}},
            },
        }

    def build_user_prompt(self, task: str, state: SharedState) -> str:
        return json.dumps({"task": task, "deliverables_contract": state.goal_profile.constraints if state.goal_profile else [], "shared_state": {"goal_profile": state.goal_profile.model_dump() if state.goal_profile else None, "project_board": state.project_board, "target_supervisors": state.target_supervisors, "drafts": state.drafts}}, indent=2)

    def run(self, task: str, state: SharedState) -> NarrativeWriterOutput:
        if self._fallback_mode:
            primary_target = "Supervisor"
            institution = "target lab"
            if state.target_supervisors:
                primary = state.target_supervisors[0].get("targets", [{}])[0]
                primary_target = primary.get("name", primary_target)
                institution = primary.get("institution", institution)
            payload = {
                "document_type": "supervisor_outreach_email",
                "target_audience": f"{primary_target} at {institution}",
                "tone": "concise, rigorous, collegial",
                "drafts": [{"version_name": "direct_fit_intro", "text": f"Task: {task}\n\nDear Prof. {primary_target},\n\nI am preparing a first PhD project on low-compute probes for predicting reasoning failures in LLM traces.\n\nBest regards,\n[Your Name]"}],
                "customization_slots": ["Insert one specific recent paper/theme from the target lab", "Insert one sentence linking your prior experience to the proposed method"],
                "weak_sentences_to_avoid": ["I am passionate about AI.", "Your research inspires me greatly."],
                "evidence": [{"claim": "Draft references selected target and project context", "source": "state.target_supervisors + state.project_board + task", "confidence": "high"}],
            }
            return self.output_model.model_validate(payload)
        return super().run(task=task, state=state)
