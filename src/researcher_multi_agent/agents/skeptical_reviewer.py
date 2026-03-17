from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.schemas.agent_outputs import GoalDeliverables, SkepticalReviewerOutput
from researcher_multi_agent.schemas.state import SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class SkepticalReviewer(DeterministicAgent[SkepticalReviewerOutput]):
    name = "SkepticalReviewer"

    def __init__(self, prompt_loader: PromptLoader) -> None:
        self.prompt = prompt_loader.load("skeptical_reviewer")

    @property
    def output_model(self) -> type[SkepticalReviewerOutput]:
        return SkepticalReviewerOutput

    def review(
        self,
        *,
        stage: str,
        state: SharedState,
        contract: GoalDeliverables,
        mode: str,
    ) -> SkepticalReviewerOutput:
        payload = self._build_review_payload(stage=stage, state=state, contract=contract, mode=mode)
        return self.output_model.model_validate(payload)

    def _stage_artifacts(self, stage: str, state: SharedState) -> list[dict]:
        field_by_stage = {
            "TopicStrategist": "topic_pool",
            "LiteratureCartographer": "reading_board",
            "ProjectArchitect": "project_board",
            "SupervisorMapper": "target_supervisors",
            "NarrativeWriter": "drafts",
            "final": "drafts",
        }
        field_name = field_by_stage.get(stage)
        if field_name is None:
            return []
        artifacts = getattr(state, field_name)
        return artifacts if isinstance(artifacts, list) else []

    def _build_review_payload(self, stage: str, state: SharedState, contract: GoalDeliverables, mode: str) -> dict:
        artifacts = self._stage_artifacts(stage=stage, state=state)
        critical_issues: list[str] = []
        minor_issues: list[str] = []
        unsupported_claims: list[str] = []
        revision_instructions: list[str] = []

        if not artifacts:
            return {
                "verdict": "REVISE",
                "critical_issues": [f"Missing required artifact for {stage}."],
                "minor_issues": [],
                "unsupported_claims": [],
                "revision_instructions": [f"Run {stage} and store its artifact in shared state."],
                "confidence": "high",
            }

        serialized = " ".join(str(item) for item in artifacts).lower()

        # 1) Deliverables completeness (MAP vs NARROW contract).
        missing_must_include = [item for item in contract.must_include if item.lower() not in serialized]
        if mode == "MAP" and stage in {"LiteratureCartographer", "final"} and not state.reading_board:
            missing_must_include.append("literature mapping output")
        if mode == "NARROW" and stage in {"ProjectArchitect", "NarrativeWriter", "final"} and not state.project_board:
            missing_must_include.append("project plan output")
        if missing_must_include:
            critical_issues.append("Deliverables incomplete: missing required contract items.")
            revision_instructions.append(
                "Address these must_include gaps: " + "; ".join(missing_must_include[:3])
            )

        # 2) Evidence coverage.
        evidence_items = []
        for artifact in artifacts:
            if isinstance(artifact, dict):
                evidence = artifact.get("evidence", [])
                if isinstance(evidence, list):
                    evidence_items.extend(evidence)
        if stage != "NarrativeWriter" and not evidence_items:
            unsupported_claims.append("Key claims are not grounded by explicit evidence sources.")
            revision_instructions.append("Add at least 2 concrete sources in the evidence field supporting major claims.")

        # 3) Non-genericity check.
        generic_tokens = ["tbd", "placeholder", "lorem ipsum", "to be decided", "generic"]
        if any(token in serialized for token in generic_tokens):
            critical_issues.append("Output contains generic/placeholder wording.")
            revision_instructions.append("Replace placeholders with specific names, claims, and scoped actions.")

        # 4) Language match (it-IT if requested).
        constraints = state.goal_profile.constraints if state.goal_profile is not None else []
        wants_italian = any("it-it" in constraint.lower() for constraint in constraints)
        if wants_italian and stage in {"NarrativeWriter", "final"}:
            italian_markers = [" il ", " la ", " per ", " con ", " e ", " grazie"]
            if not any(marker in f" {serialized} " for marker in italian_markers):
                critical_issues.append("Language mismatch: user requested it-IT output.")
                revision_instructions.append("Rewrite the draft in Italian (it-IT), preserving the same factual content.")

        if critical_issues:
            return {
                "verdict": "REJECT" if len(critical_issues) >= 2 else "REVISE",
                "critical_issues": critical_issues,
                "minor_issues": minor_issues,
                "unsupported_claims": unsupported_claims,
                "revision_instructions": revision_instructions
                or ["Resolve reviewer issues and resubmit this stage."],
                "confidence": "high",
            }

        if unsupported_claims:
            return {
                "verdict": "REVISE",
                "critical_issues": [],
                "minor_issues": ["Evidence grounding needs improvement."],
                "unsupported_claims": unsupported_claims,
                "revision_instructions": revision_instructions
                or ["Add supporting sources for every central claim and resubmit."],
                "confidence": "medium",
            }

        return {
            "verdict": "PASS",
            "critical_issues": [],
            "minor_issues": ["Output is specific and evidence-aware."],
            "unsupported_claims": [],
            "revision_instructions": [],
            "confidence": "medium",
        }

    def _build_payload(self, task: str, state: SharedState) -> dict:
        if task.startswith("Review gate for "):
            stage = task.removeprefix("Review gate for ").removesuffix(".")
            fallback_contract = GoalDeliverables(must_include=[], nice_to_have=[])
            return self._build_review_payload(stage=stage, state=state, contract=fallback_contract, mode="NARROW")

        if task.startswith("Final review"):
            fallback_contract = GoalDeliverables(must_include=[], nice_to_have=[])
            return self._build_review_payload(stage="final", state=state, contract=fallback_contract, mode="NARROW")

        stage_requirements = {
            "TopicStrategist": ("topic_pool", "candidate directions from TopicStrategist"),
            "LiteratureCartographer": ("reading_board", "literature map from LiteratureCartographer"),
            "ProjectArchitect": ("project_board", "project design from ProjectArchitect"),
            "SupervisorMapper": ("target_supervisors", "supervisor targeting from SupervisorMapper"),
            "NarrativeWriter": ("drafts", "outreach draft from NarrativeWriter"),
        }

        review_gate_prefix = "Review gate for "
        if task.startswith(review_gate_prefix):
            stage = task.removeprefix(review_gate_prefix).removesuffix(".")
            requirement = stage_requirements.get(stage)
            if requirement is not None:
                field_name, label = requirement
                if getattr(state, field_name):
                    return {
                        "verdict": "PASS",
                        "critical_issues": [],
                        "minor_issues": [],
                        "unsupported_claims": [],
                        "revision_instructions": [],
                        "confidence": "medium",
                    }
                return {
                    "verdict": "REVISE",
                    "critical_issues": [f"Missing required artifact: {label}."],
                    "minor_issues": [],
                    "unsupported_claims": [],
                    "revision_instructions": [f"Run {stage} and resubmit for review."],
                    "confidence": "high",
                }

        if state.drafts:
            return {
                "verdict": "PASS",
                "critical_issues": [],
                "minor_issues": ["Next step: tailor final draft per supervisor profile."],
                "unsupported_claims": [],
                "revision_instructions": ["Proceed with customization and sending strategy."],
                "confidence": "medium",
            }

        if state.topic_pool:
            return {
                "verdict": "REVISE",
                "critical_issues": ["Planning pipeline incomplete: no outreach draft available."],
                "minor_issues": [],
                "unsupported_claims": [],
                "revision_instructions": ["Complete remaining stages before final review."],
                "confidence": "high",
            }

        return {
            "verdict": "REVISE",
            "critical_issues": ["No candidate direction available for substantive review."],
            "minor_issues": [],
            "unsupported_claims": [],
            "revision_instructions": ["Run TopicStrategist first and resubmit."],
            "confidence": "high",
        }
