import json

from researcher_multi_agent.agents.llm_base import LLMAgent
from typing import Any
from researcher_multi_agent.schemas.agent_outputs import TopicStrategistOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class TopicStrategist(LLMAgent[TopicStrategistOutput]):
    name = "TopicStrategist"

    def __init__(self, prompt_loader: PromptLoader, llm_client: Any | None = None) -> None:
        self._fallback_mode = llm_client is None
        if llm_client is None:
            self.prompt = prompt_loader.load("topic_strategist")
            self.llm_client = None
            return
        super().__init__(llm_client=llm_client, prompt=prompt_loader.load("topic_strategist"))

    @property
    def output_model(self) -> type[TopicStrategistOutput]:
        return TopicStrategistOutput

    @property
    def output_schema(self) -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["candidate_directions", "recommended_focus", "decisive_next_questions", "evidence"],
            "properties": {
                "candidate_directions": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["name", "problem_statement", "core_hypothesis", "scorecard", "why_promising", "why_risky", "kill_criteria", "first_paper_angle"], "properties": {"name": {"type": "string"}, "problem_statement": {"type": "string"}, "core_hypothesis": {"type": "string"}, "scorecard": {"type": "object", "additionalProperties": False, "required": ["bottleneck_value", "tractability", "measurability", "novelty", "lab_fit", "first_project_strength"], "properties": {"bottleneck_value": {"type": "integer", "minimum": 1, "maximum": 5}, "tractability": {"type": "integer", "minimum": 1, "maximum": 5}, "measurability": {"type": "integer", "minimum": 1, "maximum": 5}, "novelty": {"type": "integer", "minimum": 1, "maximum": 5}, "lab_fit": {"type": "integer", "minimum": 1, "maximum": 5}, "first_project_strength": {"type": "integer", "minimum": 1, "maximum": 5}}}, "why_promising": {"type": "array", "items": {"type": "string"}}, "why_risky": {"type": "array", "items": {"type": "string"}}, "kill_criteria": {"type": "array", "items": {"type": "string"}}, "first_paper_angle": {"type": "string"}}}},
                "recommended_focus": {"type": "array", "items": {"type": "string"}},
                "decisive_next_questions": {"type": "array", "items": {"type": "string"}},
                "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["claim", "source", "confidence"], "properties": {"claim": {"type": "string"}, "source": {"type": "string"}, "confidence": {"type": "string", "enum": ["low", "medium", "high"]}}}},
            },
        }

    def build_user_prompt(self, task: str, state: SharedState) -> str:
        payload = {
            "task": task,
            "deliverables_contract": state.goal_profile.constraints if state.goal_profile else [],
            "shared_state": {
                "goal_profile": state.goal_profile.model_dump() if state.goal_profile else None,
                "topic_pool": state.topic_pool,
                "reading_board": state.reading_board,
            },
        }
        return json.dumps(payload, indent=2)

    def run(self, task: str, state: SharedState) -> TopicStrategistOutput:
        if self._fallback_mode:
            payload = {
                "candidate_directions": [
                    {
                        "name": "Compute-bounded oversight probes for reasoning models",
                        "problem_statement": f"Task scope: {task}. Design lightweight probes that predict long-horizon reasoning failures.",
                        "core_hypothesis": "Intermediate trace features can predict failure modes with less compute than verifier models.",
                        "scorecard": {"bottleneck_value": 5, "tractability": 4, "measurability": 5, "novelty": 4, "lab_fit": 5, "first_project_strength": 5},
                        "why_promising": ["Targets monitorability bottleneck directly", "Can be benchmarked on open reasoning datasets"],
                        "why_risky": ["Signal may overfit to one model family"],
                        "kill_criteria": ["Probe accuracy not better than simple uncertainty baseline"],
                        "first_paper_angle": "A compact oversight probe beats entropy baselines for predicting failed reasoning trajectories.",
                    }
                ],
                "recommended_focus": ["Compute-bounded oversight probes for reasoning models"],
                "decisive_next_questions": ["Which publicly available reasoning traces are rich enough for supervision?", "What failure definition is stable across tasks?"],
                "evidence": [{"claim": "Reasoning traces enable failure prediction", "source": "shared_state.goal_profile + task", "confidence": "medium"}],
            }
            return self.output_model.model_validate(payload)
        return super().run(task=task, state=state)
