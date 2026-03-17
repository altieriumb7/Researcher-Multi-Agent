import json
from collections import Counter

from researcher_multi_agent.agents.llm_base import LLMAgent
from typing import Any
from researcher_multi_agent.schemas.agent_outputs import LiteratureCartographerOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class LiteratureCartographer(LLMAgent[LiteratureCartographerOutput]):
    name = "LiteratureCartographer"
    BRANCH_SAMPLES = 3

    def __init__(self, prompt_loader: PromptLoader, llm_client: Any | None = None) -> None:
        self._fallback_mode = llm_client is None
        if llm_client is None:
            self.prompt = prompt_loader.load("literature_cartographer")
            self.llm_client = None
            return
        super().__init__(llm_client=llm_client, prompt=prompt_loader.load("literature_cartographer"))

    @property
    def output_model(self) -> type[LiteratureCartographerOutput]:
        return LiteratureCartographerOutput

    @property
    def output_schema(self) -> dict:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["topic", "clusters", "must_read", "optional_read", "benchmark_map", "evidence_gaps", "reading_ladder", "evidence"],
            "properties": {
                "topic": {"type": "string"},
                "clusters": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["cluster_name", "why_it_matters", "key_papers", "benchmarks", "methods", "open_disputes"], "properties": {"cluster_name": {"type": "string"}, "why_it_matters": {"type": "string"}, "key_papers": {"type": "array", "items": {"type": "string"}}, "benchmarks": {"type": "array", "items": {"type": "string"}}, "methods": {"type": "array", "items": {"type": "string"}}, "open_disputes": {"type": "array", "items": {"type": "string"}}}}},
                "must_read": {"type": "array", "items": {"type": "string"}},
                "optional_read": {"type": "array", "items": {"type": "string"}},
                "benchmark_map": {"type": "array", "items": {"type": "string"}},
                "evidence_gaps": {"type": "array", "items": {"type": "string"}},
                "reading_ladder": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["day", "goal", "papers", "notes_to_extract"], "properties": {"day": {"type": "integer"}, "goal": {"type": "string"}, "papers": {"type": "array", "items": {"type": "string"}}, "notes_to_extract": {"type": "array", "items": {"type": "string"}}}}},
                "evidence": {"type": "array", "items": {"type": "object", "additionalProperties": False, "required": ["claim", "source", "confidence"], "properties": {"claim": {"type": "string"}, "source": {"type": "string"}, "confidence": {"type": "string", "enum": ["low", "medium", "high"]}}}},
            },
        }

    def build_user_prompt(self, task: str, state: SharedState) -> str:
        return json.dumps({"task": task, "deliverables_contract": state.goal_profile.constraints if state.goal_profile else [], "shared_state": {"goal_profile": state.goal_profile.model_dump() if state.goal_profile else None, "topic_pool": state.topic_pool, "reading_board": state.reading_board}}, indent=2)

    def run(self, task: str, state: SharedState) -> LiteratureCartographerOutput:
        topic_signal = self._topic_agreement_signal(state)
        if self._fallback_mode:
            topic_name = state.topic_pool[0].get("recommended_focus", ["Compute-bounded oversight probes"])[0] if state.topic_pool else "Compute-bounded oversight probes for reasoning models"
            base_payload = {
                "topic": f"{topic_name} ({task})",
                "clusters": [{"cluster_name": "Reasoning failure detection and confidence proxies", "why_it_matters": "Defines practical baselines for predicting failures before final answers.", "key_papers": ["Cobbe et al. (2021) GSM8K", "Lightman et al. (2023) Let's Verify Step by Step"], "benchmarks": ["GSM8K", "MATH", "StrategyQA"], "methods": ["process supervision", "uncertainty scoring", "verifier models"], "open_disputes": ["Whether process-level labels transfer across model families"]}],
                "must_read": ["Lightman et al. (2023)", "Cobbe et al. (2021)"],
                "optional_read": ["Weng et al. (2024) on monitoring LLM reasoning"],
                "benchmark_map": ["GSM8K: arithmetic multi-step reasoning, accuracy-focused", "MATH: high-difficulty symbolic reasoning, final-answer scoring"],
                "evidence_gaps": ["Few papers compare low-compute probes against verifier-style baselines on identical failure definitions"],
                "reading_ladder": [{"day": 1, "goal": "Understand failure taxonomy and datasets", "papers": ["Cobbe et al. (2021)", "Lightman et al. (2023)"], "notes_to_extract": ["Failure definitions", "label quality", "evaluation setup"]}],
                "evidence": [{"claim": "Selected papers are foundational for reasoning-failure mapping", "source": "state.topic_pool + task", "confidence": "medium"}],
            }
            alternatives = [base_payload for _ in range(self.BRANCH_SAMPLES)]
        else:
            alternatives = []
            for sample_idx in range(1, self.BRANCH_SAMPLES + 1):
                user_prompt = (
                    f"{self.build_user_prompt(task=task, state=state)}\n\n"
                    "You are in bounded branching mode for MAP exploration. "
                    f"Return an intentionally distinct literature clustering sample {sample_idx}/{self.BRANCH_SAMPLES}."
                )
                result = self.llm_client.call_json_schema(system=self.prompt, user=user_prompt, json_schema=self.output_schema)
                alternatives.append(result.parsed_json)

        best = max(alternatives, key=self._selection_score)
        best["evidence"] = [*best.get("evidence", []), topic_signal]
        return self.output_model.model_validate(best)

    def _selection_score(self, payload: dict[str, Any]) -> int:
        cluster_depth = sum(
            len(cluster.get("key_papers", [])) + len(cluster.get("open_disputes", [])) + len(cluster.get("benchmarks", []))
            for cluster in payload.get("clusters", [])
        )
        ladder_coverage = sum(len(step.get("papers", [])) for step in payload.get("reading_ladder", []))
        return cluster_depth + ladder_coverage + len(payload.get("evidence_gaps", []))

    def _topic_agreement_signal(self, state: SharedState) -> dict[str, str]:
        if not state.topic_pool:
            return {
                "claim": "No upstream topic samples were available; using default topic anchor.",
                "source": "state.topic_pool",
                "confidence": "low",
            }

        focus_counter = Counter(
            focus.strip().lower()
            for item in state.topic_pool
            for focus in item.get("recommended_focus", [])
            if isinstance(focus, str) and focus.strip()
        )
        if not focus_counter:
            return {
                "claim": "Topic sample agreement could not be computed because recommended_focus was empty.",
                "source": "state.topic_pool.recommended_focus",
                "confidence": "low",
            }

        focus, votes = focus_counter.most_common(1)[0]
        return {
            "claim": f"Upstream topic self-consistency: '{focus}' appeared in {votes}/{len(state.topic_pool)} topic samples.",
            "source": "TopicStrategist branching outputs",
            "confidence": "high" if votes >= max(2, len(state.topic_pool) - 1) else "medium",
        }
