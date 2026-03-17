from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import GoalIntentOutput
from researcher_multi_agent.schemas.state import SharedState


class GoalInterpreter(DeterministicAgent[GoalIntentOutput]):
    name = "GoalInterpreter"

    MAP_HINTS = ("hot topics", "where treated", "which company", "universities")
    NARROW_HINTS = ("pick one direction", "thesis", "first paper", "supervisor outreach")

    @property
    def output_model(self) -> type[GoalIntentOutput]:
        return GoalIntentOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        lowered_goal = task.lower()

        matched_map_hints = [hint for hint in self.MAP_HINTS if hint in lowered_goal]
        matched_narrow_hints = [hint for hint in self.NARROW_HINTS if hint in lowered_goal]

        assumptions: list[str] = []
        questions_to_user_optional: list[str] = []

        if matched_narrow_hints and not matched_map_hints:
            mode = "NARROW"
        elif matched_map_hints and not matched_narrow_hints:
            mode = "MAP"
        elif matched_map_hints and matched_narrow_hints:
            mode = "NARROW"
            assumptions.append(
                "The goal includes both mapping and narrowing cues; prioritizing NARROW to produce a concrete first step."
            )
        else:
            mode = "MAP"
            assumptions.append(
                "The goal phrasing did not clearly match MAP or NARROW triggers, so defaulting to MAP."
            )
            questions_to_user_optional = [
                "Do you want a landscape map first, or should we commit to one thesis direction now?",
                "Are you optimizing for exploration breadth or first-paper execution speed?",
            ]

        return {
            "mode": mode,
            "deliverables": {
                "must_include": [
                    "Explicit decomposition of the user goal into actionable outputs.",
                    "A sequence of delegated tasks aligned to the selected mode.",
                ],
                "nice_to_have": [
                    "One-paragraph rationale for why this mode fits the goal.",
                    "Potential pivots if early evidence contradicts assumptions.",
                ],
            },
            "success_criteria": [
                "The plan output is aligned with the selected MAP/NARROW mode.",
                "At least one concrete next action can be executed immediately.",
            ],
            "questions_to_user_optional": questions_to_user_optional,
            "assumptions": assumptions,
        }
