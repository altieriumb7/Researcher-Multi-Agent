import json

from researcher_multi_agent.agents.llm_base import LLMAgent
from typing import Any
from researcher_multi_agent.schemas.agent_outputs import SupervisorMapperOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class SupervisorMapper(LLMAgent[SupervisorMapperOutput]):
    name = "SupervisorMapper"

    def __init__(self, prompt_loader: PromptLoader, llm_client: Any | None = None) -> None:
        self._fallback_mode = llm_client is None
        if llm_client is None:
            self.prompt = prompt_loader.load("supervisor_mapper")
            self.llm_client = None
            return
        super().__init__(llm_client=llm_client, prompt=prompt_loader.load("supervisor_mapper"))

    @property
    def output_model(self) -> type[SupervisorMapperOutput]:
        return SupervisorMapperOutput

    @property
    def output_schema(self) -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["targets", "segmentation", "evidence"],
            "properties": {
                "targets": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["name", "institution", "fit_level", "fit_reasons", "relevant_themes_to_mention", "best_outreach_angle", "risks_or_red_flags", "priority"], "properties": {"name": {"type": "string"}, "institution": {"type": "string"}, "fit_level": {"type": "string", "enum": ["primary", "adjacent", "opportunistic"]}, "fit_reasons": {"type": "array", "items": {"type": "string"}}, "relevant_themes_to_mention": {"type": "array", "items": {"type": "string"}}, "best_outreach_angle": {"type": "string"}, "risks_or_red_flags": {"type": "array", "items": {"type": "string"}}, "priority": {"type": "integer", "minimum": 1}}}},
                "segmentation": {"type": "object", "additionalProperties": False, "required": ["reach", "strong_fit", "safe_fit"], "properties": {"reach": {"type": "array", "items": {"type": "string"}}, "strong_fit": {"type": "array", "items": {"type": "string"}}, "safe_fit": {"type": "array", "items": {"type": "string"}}}},
                "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["claim", "source", "confidence"], "properties": {"claim": {"type": "string"}, "source": {"type": "string"}, "confidence": {"type": "string", "enum": ["low", "medium", "high"]}}}},
            },
        }

    def build_user_prompt(self, task: str, state: SharedState) -> str:
        return json.dumps({"task": task, "deliverables_contract": state.goal_profile.constraints if state.goal_profile else [], "shared_state": {"goal_profile": state.goal_profile.model_dump() if state.goal_profile else None, "project_board": state.project_board, "target_supervisors": state.target_supervisors}}, indent=2)

    def run(self, task: str, state: SharedState) -> SupervisorMapperOutput:
        if self._fallback_mode:
            project_title = state.project_board[0].get("project_title", "Low-compute oversight probes") if state.project_board else "Low-compute oversight probes"
            payload = {
                "targets": [
                    {"name": "Supervisor A", "institution": "University Alpha", "fit_level": "primary", "fit_reasons": ["Recent lab outputs on verifier-lite oversight methods", f"Task: {task} | Project '{project_title}' aligns with ongoing work on reasoning reliability"], "relevant_themes_to_mention": ["process-level failure prediction", "cost-constrained evaluation for oversight"], "best_outreach_angle": "Propose a scoped first experiment comparing low-compute probes against entropy baselines.", "risks_or_red_flags": ["Large lab; response rates may be lower without clear novelty"], "priority": 1},
                    {"name": "Supervisor B", "institution": "Institute Beta", "fit_level": "adjacent", "fit_reasons": ["Focus on robust evaluation under distribution shift", "Methodological overlap in uncertainty and calibration"], "relevant_themes_to_mention": ["cross-dataset transfer stress tests", "calibration under shift"], "best_outreach_angle": "Frame collaboration around evaluating transfer robustness of probe-based risk scoring.", "risks_or_red_flags": ["Topic overlap may be broader than direct core-lab focus"], "priority": 2},
                ],
                "segmentation": {"reach": [], "strong_fit": ["Supervisor A"], "safe_fit": ["Supervisor B"]},
                "evidence": [{"claim": "Primary target aligns with project method", "source": "state.project_board + task", "confidence": "medium"}],
            }
            return self.output_model.model_validate(payload)
        return super().run(task=task, state=state)
