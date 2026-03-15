from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import ChiefOfStaffOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class ChiefOfStaff(DeterministicAgent[ChiefOfStaffOutput]):
    name = "ChiefOfStaff"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("chief_of_staff")

    @property
    def output_model(self) -> type[ChiefOfStaffOutput]:
        return ChiefOfStaffOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        has_topic = bool(state.topic_pool)
        has_literature_map = bool(state.reading_board)
        has_project_design = bool(state.project_board)
        has_supervisor_targets = bool(state.target_supervisors)
        has_drafts = bool(state.drafts)
        delegations = []

        if not has_topic:
            delegations.append(
                {
                    "agent": "TopicStrategist",
                    "task": f"Narrow the goal into concrete directions: {task}",
                    "why_this_agent": "Goal is broad and needs precise research framing.",
                    "priority": "high",
                    "expected_output": "Scored candidate directions and recommended focus.",
                }
            )

        if not has_literature_map:
            delegations.append(
                {
                    "agent": "LiteratureCartographer",
                    "task": "Build a literature map and a short reading ladder for the selected topic.",
                    "why_this_agent": "Need an evidence and benchmark map to ground next project decisions.",
                    "priority": "medium",
                    "expected_output": "Clustered literature map, benchmark map, and reading ladder.",
                }
            )

        if not has_project_design:
            delegations.append(
                {
                    "agent": "ProjectArchitect",
                    "task": "Design a feasible first project grounded in the mapped literature.",
                    "why_this_agent": "Need a concrete, falsifiable project plan after literature grounding.",
                    "priority": "low",
                    "expected_output": "Structured project design with methods, baselines, metrics, and timeline.",
                }
            )

        if not has_supervisor_targets:
            delegations.append(
                {
                    "agent": "SupervisorMapper",
                    "task": "Rank supervisor/lab targets based on project fit and outreach viability.",
                    "why_this_agent": "Need evidence-based supervisor targeting after project framing.",
                    "priority": "low",
                    "expected_output": "Ranked supervisor targets with segmentation and outreach angles.",
                }
            )

        if not has_drafts:
            delegations.append(
                {
                    "agent": "NarrativeWriter",
                    "task": "Draft personalized outreach email variants grounded in project and supervisor fit.",
                    "why_this_agent": "Need concise outreach drafts that are specific and evidence-grounded.",
                    "priority": "low",
                    "expected_output": "Structured outreach drafts with customization slots.",
                }
            )

        return {
            "goal_now": "Create a narrow research direction and quality-check it.",
            "assumptions": ["The user goal is still broad and exploratory."],
            "delegations": delegations,
            "merged_plan": {
                "now": ["Run TopicStrategist", "Run LiteratureCartographer", "Run ProjectArchitect", "Run SupervisorMapper", "Run NarrativeWriter", "Run SkepticalReviewer"],
                "parallel": [],
                "later": [],
            },
            "risks": ["Topic may remain too vague without strict criteria."],
            "state_update": {
                "goal_profile": state.goal_profile.model_dump() if state.goal_profile else {},
            },
        }
