import json

from researcher_multi_agent.agents.llm_base import LLMAgent
from typing import Any
from researcher_multi_agent.schemas.agent_outputs import ProjectArchitectOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class ProjectArchitect(LLMAgent[ProjectArchitectOutput]):
    name = "ProjectArchitect"

    def __init__(self, prompt_loader: PromptLoader, llm_client: Any | None = None) -> None:
        self._fallback_mode = llm_client is None
        if llm_client is None:
            self.prompt = prompt_loader.load("project_architect")
            self.llm_client = None
            return
        super().__init__(llm_client=llm_client, prompt=prompt_loader.load("project_architect"))

    @property
    def output_model(self) -> type[ProjectArchitectOutput]:
        return ProjectArchitectOutput

    @property
    def output_schema(self) -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["project_title", "research_question", "hypothesis", "minimal_publishable_claim", "datasets_tasks", "baselines", "method_outline", "evaluation", "resources", "timeline", "major_risks", "fallback_versions", "evidence"],
            "properties": {
                "project_title": {"type": "string"}, "research_question": {"type": "string"}, "hypothesis": {"type": "string"}, "minimal_publishable_claim": {"type": "string"},
                "datasets_tasks": {"type": "array", "items": {"type": "string"}}, "baselines": {"type": "array", "items": {"type": "string"}}, "method_outline": {"type": "array", "items": {"type": "string"}},
                "evaluation": {"type": "object", "additionalProperties": False, "required": ["primary_metrics", "secondary_metrics", "ablations", "stress_tests"], "properties": {"primary_metrics": {"type": "array", "items": {"type": "string"}}, "secondary_metrics": {"type": "array", "items": {"type": "string"}}, "ablations": {"type": "array", "items": {"type": "string"}}, "stress_tests": {"type": "array", "items": {"type": "string"}}}},
                "resources": {"type": "object", "additionalProperties": False, "required": ["compute", "data_needs", "engineering_needs"], "properties": {"compute": {"type": "string"}, "data_needs": {"type": "string"}, "engineering_needs": {"type": "string"}}},
                "timeline": {"type": "object", "additionalProperties": False, "required": ["week_1_2", "week_3_4", "week_5_8"], "properties": {"week_1_2": {"type": "array", "items": {"type": "string"}}, "week_3_4": {"type": "array", "items": {"type": "string"}}, "week_5_8": {"type": "array", "items": {"type": "string"}}}},
                "major_risks": {"type": "array", "items": {"type": "string"}}, "fallback_versions": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["claim", "source", "confidence"], "properties": {"claim": {"type": "string"}, "source": {"type": "string"}, "confidence": {"type": "string", "enum": ["low", "medium", "high"]}}}},
            },
        }

    def build_user_prompt(self, task: str, state: SharedState) -> str:
        return json.dumps({"task": task, "deliverables_contract": state.goal_profile.constraints if state.goal_profile else [], "shared_state": {"goal_profile": state.goal_profile.model_dump() if state.goal_profile else None, "topic_pool": state.topic_pool, "reading_board": state.reading_board, "project_board": state.project_board}}, indent=2)

    def run(self, task: str, state: SharedState) -> ProjectArchitectOutput:
        if self._fallback_mode:
            payload = {
                "project_title": "Low-compute probes for predicting reasoning failures",
                "research_question": f"{task} | Can intermediate-trace probes predict final reasoning errors better than entropy baselines under fixed compute budgets?",
                "hypothesis": "Compact probes over intermediate traces outperform answer-only uncertainty baselines for failure prediction.",
                "minimal_publishable_claim": "A simple probe predicts failed trajectories with higher AUROC than entropy and self-consistency baselines at matched cost.",
                "datasets_tasks": ["GSM8K", "MATH"],
                "baselines": ["token entropy", "self-consistency variance", "small verifier"],
                "method_outline": ["Extract intermediate trace features", "Train lightweight failure classifier", "Compare with answer-only baselines under budget constraints"],
                "evaluation": {"primary_metrics": ["AUROC for failure prediction", "cost-normalized AUROC"], "secondary_metrics": ["ECE", "precision@k for risky samples"], "ablations": ["feature groups", "model family transfer"], "stress_tests": ["distribution shift from GSM8K to MATH"]},
                "resources": {"compute": "1-2 academic GPUs for 6-8 weeks", "data_needs": "Reasoning traces with correctness labels", "engineering_needs": "Data pipeline for trace extraction and evaluation"},
                "timeline": {"week_1_2": ["dataset curation", "failure definition finalization"], "week_3_4": ["baseline reproduction", "probe implementation"], "week_5_8": ["full experiments", "ablation/stress tests", "paper draft"]},
                "major_risks": ["Trace features may not generalize across model families"],
                "fallback_versions": ["Single-dataset scoped evaluation with stronger ablations"],
                "evidence": [{"claim": "Matched-cost evaluation is necessary for fair comparison", "source": "state.reading_board + task", "confidence": "medium"}],
            }
            return self.output_model.model_validate(payload)
        return super().run(task=task, state=state)
