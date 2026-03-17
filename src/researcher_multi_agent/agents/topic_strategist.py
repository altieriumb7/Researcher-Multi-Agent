import json
from collections import Counter

from researcher_multi_agent.agents.llm_base import LLMAgent
from typing import Any
from researcher_multi_agent.schemas.agent_outputs import TopicStrategistOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class TopicStrategist(LLMAgent[TopicStrategistOutput]):
    name = "TopicStrategist"
    BRANCH_SAMPLES = 3

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
            base_payload = {
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
            alternatives = [base_payload for _ in range(self.BRANCH_SAMPLES)]
        else:
            alternatives = []
            for sample_idx in range(1, self.BRANCH_SAMPLES + 1):
                user_prompt = (
                    f"{self.build_user_prompt(task=task, state=state)}\n\n"
                    "You are in bounded branching mode for MAP exploration. "
                    f"Return an intentionally distinct candidate set for sample {sample_idx}/{self.BRANCH_SAMPLES}."
                )
                result = self.llm_client.call_json_schema(system=self.prompt, user=user_prompt, json_schema=self.output_schema)
                alternatives.append(result.parsed_json)

        best = max(alternatives, key=self._selection_score)
        best["evidence"] = [*best.get("evidence", []), self._agreement_signal(alternatives)]
        return self.output_model.model_validate(best)

    def _selection_score(self, payload: dict[str, Any]) -> int:
        total_direction_score = sum(sum(direction.get("scorecard", {}).values()) for direction in payload.get("candidate_directions", []))
        breadth_bonus = len(payload.get("candidate_directions", [])) + len(payload.get("decisive_next_questions", []))
        return total_direction_score + breadth_bonus

    def _agreement_signal(self, alternatives: list[dict[str, Any]]) -> dict[str, str]:
        focus_counter = Counter(
            focus.strip().lower() for payload in alternatives for focus in payload.get("recommended_focus", []) if focus.strip()
        )
        if not focus_counter:
            return {
                "claim": "Self-consistency agreement across branching samples was unavailable.",
                "source": f"{self.BRANCH_SAMPLES} branching samples",
                "confidence": "low",
            }

        best_focus, best_votes = focus_counter.most_common(1)[0]
        return {
            "claim": f"Self-consistency signal: '{best_focus}' appeared in {best_votes}/{len(alternatives)} branching samples.",
            "source": f"{len(alternatives)} bounded branching samples with selector rubric: scorecard strength + question coverage",
            "confidence": "high" if best_votes >= (len(alternatives) - 1) else "medium",
        }
