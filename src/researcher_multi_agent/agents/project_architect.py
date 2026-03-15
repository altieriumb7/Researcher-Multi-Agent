from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import ProjectArchitectOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class ProjectArchitect(DeterministicAgent[ProjectArchitectOutput]):
    name = "ProjectArchitect"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("project_architect")

    @property
    def output_model(self) -> type[ProjectArchitectOutput]:
        return ProjectArchitectOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        return {
            "project_title": "Low-compute probes for predicting reasoning failures",
            "research_question": "Can intermediate-trace probes predict final reasoning errors better than entropy baselines under fixed compute budgets?",
            "hypothesis": "Compact probes over intermediate traces outperform answer-only uncertainty baselines for failure prediction.",
            "minimal_publishable_claim": "A simple probe predicts failed trajectories with higher AUROC than entropy and self-consistency baselines at matched cost.",
            "datasets_tasks": ["GSM8K", "MATH"],
            "baselines": ["token entropy", "self-consistency variance", "small verifier"],
            "method_outline": [
                "Extract intermediate trace features",
                "Train lightweight failure classifier",
                "Compare with answer-only baselines under budget constraints",
            ],
            "evaluation": {
                "primary_metrics": ["AUROC for failure prediction", "cost-normalized AUROC"],
                "secondary_metrics": ["ECE", "precision@k for risky samples"],
                "ablations": ["feature groups", "model family transfer"],
                "stress_tests": ["distribution shift from GSM8K to MATH"],
            },
            "resources": {
                "compute": "1-2 academic GPUs for 6-8 weeks",
                "data_needs": "Reasoning traces with correctness labels",
                "engineering_needs": "Data pipeline for trace extraction and evaluation",
            },
            "timeline": {
                "week_1_2": ["dataset curation", "failure definition finalization"],
                "week_3_4": ["baseline reproduction", "probe implementation"],
                "week_5_8": ["full experiments", "ablation/stress tests", "paper draft"],
            },
            "major_risks": ["Trace features may not generalize across model families"],
            "fallback_versions": ["Single-dataset scoped evaluation with stronger ablations"],
        }
