from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import SupervisorMapperOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class SupervisorMapper(DeterministicAgent[SupervisorMapperOutput]):
    name = "SupervisorMapper"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("supervisor_mapper")

    @property
    def output_model(self) -> type[SupervisorMapperOutput]:
        return SupervisorMapperOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        project_title = (
            state.project_board[0].get("project_title", "Low-compute oversight probes")
            if state.project_board
            else "Low-compute oversight probes"
        )

        return {
            "targets": [
                {
                    "name": "Supervisor A",
                    "institution": "University Alpha",
                    "fit_level": "primary",
                    "fit_reasons": [
                        "Recent lab outputs on verifier-lite oversight methods",
                        f"Project '{project_title}' aligns with ongoing work on reasoning reliability",
                    ],
                    "relevant_themes_to_mention": [
                        "process-level failure prediction",
                        "cost-constrained evaluation for oversight",
                    ],
                    "best_outreach_angle": "Propose a scoped first experiment comparing low-compute probes against entropy baselines.",
                    "risks_or_red_flags": ["Large lab; response rates may be lower without clear novelty"],
                    "priority": 1,
                },
                {
                    "name": "Supervisor B",
                    "institution": "Institute Beta",
                    "fit_level": "adjacent",
                    "fit_reasons": [
                        "Focus on robust evaluation under distribution shift",
                        "Methodological overlap in uncertainty and calibration",
                    ],
                    "relevant_themes_to_mention": ["cross-dataset transfer stress tests", "calibration under shift"],
                    "best_outreach_angle": "Frame collaboration around evaluating transfer robustness of probe-based risk scoring.",
                    "risks_or_red_flags": ["Topic overlap may be broader than direct core-lab focus"],
                    "priority": 2,
                },
                {
                    "name": "Supervisor C",
                    "institution": "Lab Gamma",
                    "fit_level": "opportunistic",
                    "fit_reasons": ["Works on scalable alignment methods", "Could host a practical benchmark-oriented project"],
                    "relevant_themes_to_mention": ["pragmatic first-paper scope", "benchmark-first execution"],
                    "best_outreach_angle": "Pitch a concise first-paper plan with explicit compute budget and milestones.",
                    "risks_or_red_flags": ["Fit depends on current lab intake and project bandwidth"],
                    "priority": 3,
                },
            ],
            "segmentation": {
                "reach": ["Supervisor C"],
                "strong_fit": ["Supervisor A"],
                "safe_fit": ["Supervisor B"],
            },
        }
