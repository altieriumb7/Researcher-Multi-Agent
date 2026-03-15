from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import LiteratureCartographerOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class LiteratureCartographer(DeterministicAgent[LiteratureCartographerOutput]):
    name = "LiteratureCartographer"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("literature_cartographer")

    @property
    def output_model(self) -> type[LiteratureCartographerOutput]:
        return LiteratureCartographerOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        topic_name = (
            state.topic_pool[0].get("recommended_focus", ["Compute-bounded oversight probes"])[0]
            if state.topic_pool
            else "Compute-bounded oversight probes for reasoning models"
        )
        return {
            "topic": topic_name,
            "clusters": [
                {
                    "cluster_name": "Reasoning failure detection and confidence proxies",
                    "why_it_matters": "Defines practical baselines for predicting failures before final answers are emitted.",
                    "key_papers": [
                        "Cobbe et al. (2021) GSM8K",
                        "Lightman et al. (2023) Let's Verify Step by Step",
                    ],
                    "benchmarks": ["GSM8K", "MATH", "StrategyQA"],
                    "methods": ["process supervision", "uncertainty scoring", "verifier models"],
                    "open_disputes": ["Whether process-level labels transfer across model families"],
                }
            ],
            "must_read": ["Lightman et al. (2023)", "Cobbe et al. (2021)"],
            "optional_read": ["Weng et al. (2024) on monitoring LLM reasoning"],
            "benchmark_map": [
                "GSM8K: arithmetic multi-step reasoning, accuracy-focused",
                "MATH: high-difficulty symbolic reasoning, final-answer scoring",
            ],
            "evidence_gaps": [
                "Few papers compare low-compute probes against verifier-style baselines on identical failure definitions"
            ],
            "reading_ladder": [
                {
                    "day": 1,
                    "goal": "Understand failure taxonomy and datasets",
                    "papers": ["Cobbe et al. (2021)", "Lightman et al. (2023)"],
                    "notes_to_extract": ["Failure definitions", "label quality", "evaluation setup"],
                },
                {
                    "day": 2,
                    "goal": "Map baseline methods and costs",
                    "papers": ["Selected verifier and uncertainty-baseline papers"],
                    "notes_to_extract": ["compute footprint", "model access assumptions"],
                },
            ],
        }
