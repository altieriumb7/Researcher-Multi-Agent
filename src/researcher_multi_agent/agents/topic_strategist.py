from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import TopicStrategistOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class TopicStrategist(DeterministicAgent[TopicStrategistOutput]):
    name = "TopicStrategist"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("topic_strategist")

    @property
    def output_model(self) -> type[TopicStrategistOutput]:
        return TopicStrategistOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        return {
            "candidate_directions": [
                {
                    "name": "Compute-bounded oversight probes for reasoning models",
                    "problem_statement": "Design lightweight probes that predict long-horizon reasoning failures before final outputs.",
                    "core_hypothesis": "Intermediate trace features can predict failure modes with less compute than full verifier models.",
                    "scorecard": {
                        "bottleneck_value": 5,
                        "tractability": 4,
                        "measurability": 5,
                        "novelty": 4,
                        "lab_fit": 5,
                        "first_project_strength": 5,
                    },
                    "why_promising": [
                        "Targets monitorability bottleneck directly",
                        "Can be benchmarked on open reasoning datasets",
                    ],
                    "why_risky": ["Signal may overfit to one model family"],
                    "kill_criteria": ["Probe accuracy not better than simple uncertainty baseline"],
                    "first_paper_angle": "A compact oversight probe beats entropy baselines for predicting failed reasoning trajectories.",
                }
            ],
            "recommended_focus": ["Compute-bounded oversight probes for reasoning models"],
            "decisive_next_questions": [
                "Which publicly available reasoning traces are rich enough for supervision?",
                "What failure definition is stable across tasks?",
            ],
        }
