from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from researcher_multi_agent.schemas.validation import (
    SchemaValidationError,
    require_fields,
    require_int_range,
    require_list_of_str,
    require_literal,
    require_type,
)


SCORECARD_KEYS = {
    "bottleneck_value",
    "tractability",
    "measurability",
    "novelty",
    "lab_fit",
    "first_project_strength",
}


@dataclass
class Delegation:
    agent: str
    task: str
    why_this_agent: str
    priority: str
    expected_output: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Delegation":
        require_fields(
            payload,
            ["agent", "task", "why_this_agent", "priority", "expected_output"],
            "Delegation",
        )
        require_literal(payload["priority"], {"high", "medium", "low"}, "Delegation.priority")
        require_type(payload["agent"], str, "Delegation.agent")
        require_type(payload["task"], str, "Delegation.task")
        require_type(payload["why_this_agent"], str, "Delegation.why_this_agent")
        require_type(payload["expected_output"], str, "Delegation.expected_output")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MergedPlan:
    now: list[str]
    parallel: list[str]
    later: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MergedPlan":
        require_fields(payload, ["now", "parallel", "later"], "MergedPlan")
        require_list_of_str(payload["now"], "MergedPlan.now")
        require_list_of_str(payload["parallel"], "MergedPlan.parallel")
        require_list_of_str(payload["later"], "MergedPlan.later")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChiefOfStaffOutput:
    goal_now: str
    assumptions: list[str]
    delegations: list[Delegation]
    merged_plan: MergedPlan
    risks: list[str]
    state_update: dict[str, Any]

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "ChiefOfStaffOutput":
        require_fields(
            payload,
            ["goal_now", "assumptions", "delegations", "merged_plan", "risks", "state_update"],
            "ChiefOfStaffOutput",
        )
        require_type(payload["goal_now"], str, "ChiefOfStaffOutput.goal_now")
        require_list_of_str(payload["assumptions"], "ChiefOfStaffOutput.assumptions")
        require_type(payload["delegations"], list, "ChiefOfStaffOutput.delegations")
        require_list_of_str(payload["risks"], "ChiefOfStaffOutput.risks")
        require_type(payload["state_update"], dict, "ChiefOfStaffOutput.state_update")

        delegations = [Delegation.from_dict(item) for item in payload["delegations"]]
        merged_plan = MergedPlan.from_dict(payload["merged_plan"])
        return cls(
            goal_now=payload["goal_now"],
            assumptions=payload["assumptions"],
            delegations=delegations,
            merged_plan=merged_plan,
            risks=payload["risks"],
            state_update=payload["state_update"],
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "goal_now": self.goal_now,
            "assumptions": self.assumptions,
            "delegations": [d.model_dump() for d in self.delegations],
            "merged_plan": self.merged_plan.model_dump(),
            "risks": self.risks,
            "state_update": self.state_update,
        }


@dataclass
class CandidateDirection:
    name: str
    problem_statement: str
    core_hypothesis: str
    scorecard: dict[str, int]
    why_promising: list[str]
    why_risky: list[str]
    kill_criteria: list[str]
    first_paper_angle: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CandidateDirection":
        require_fields(
            payload,
            [
                "name",
                "problem_statement",
                "core_hypothesis",
                "scorecard",
                "why_promising",
                "why_risky",
                "kill_criteria",
                "first_paper_angle",
            ],
            "CandidateDirection",
        )
        require_type(payload["name"], str, "CandidateDirection.name")
        require_type(payload["problem_statement"], str, "CandidateDirection.problem_statement")
        require_type(payload["core_hypothesis"], str, "CandidateDirection.core_hypothesis")
        require_type(payload["scorecard"], dict, "CandidateDirection.scorecard")
        require_list_of_str(payload["why_promising"], "CandidateDirection.why_promising")
        require_list_of_str(payload["why_risky"], "CandidateDirection.why_risky")
        require_list_of_str(payload["kill_criteria"], "CandidateDirection.kill_criteria")
        require_type(payload["first_paper_angle"], str, "CandidateDirection.first_paper_angle")

        scorecard = payload["scorecard"]
        missing_keys = SCORECARD_KEYS - set(scorecard.keys())
        if missing_keys:
            raise SchemaValidationError(f"CandidateDirection.scorecard missing keys: {sorted(missing_keys)}")
        for key in SCORECARD_KEYS:
            require_int_range(scorecard[key], min_value=1, max_value=5, field_name=f"CandidateDirection.scorecard.{key}")

        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TopicStrategistOutput:
    candidate_directions: list[CandidateDirection]
    recommended_focus: list[str]
    decisive_next_questions: list[str]

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "TopicStrategistOutput":
        require_fields(
            payload,
            ["candidate_directions", "recommended_focus", "decisive_next_questions"],
            "TopicStrategistOutput",
        )
        require_type(payload["candidate_directions"], list, "TopicStrategistOutput.candidate_directions")
        require_list_of_str(payload["recommended_focus"], "TopicStrategistOutput.recommended_focus")
        require_list_of_str(payload["decisive_next_questions"], "TopicStrategistOutput.decisive_next_questions")

        directions = [CandidateDirection.from_dict(item) for item in payload["candidate_directions"]]
        if not directions:
            raise SchemaValidationError("TopicStrategistOutput requires at least one candidate direction")
        return cls(
            candidate_directions=directions,
            recommended_focus=payload["recommended_focus"],
            decisive_next_questions=payload["decisive_next_questions"],
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "candidate_directions": [direction.model_dump() for direction in self.candidate_directions],
            "recommended_focus": self.recommended_focus,
            "decisive_next_questions": self.decisive_next_questions,
        }


@dataclass
class SkepticalReviewerOutput:
    verdict: str
    critical_issues: list[str] = field(default_factory=list)
    minor_issues: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    revision_instructions: list[str] = field(default_factory=list)
    confidence: str = "medium"

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "SkepticalReviewerOutput":
        require_fields(
            payload,
            [
                "verdict",
                "critical_issues",
                "minor_issues",
                "unsupported_claims",
                "revision_instructions",
                "confidence",
            ],
            "SkepticalReviewerOutput",
        )
        require_literal(payload["verdict"], {"PASS", "REVISE", "REJECT"}, "SkepticalReviewerOutput.verdict")
        require_literal(payload["confidence"], {"low", "medium", "high"}, "SkepticalReviewerOutput.confidence")
        require_list_of_str(payload["critical_issues"], "SkepticalReviewerOutput.critical_issues")
        require_list_of_str(payload["minor_issues"], "SkepticalReviewerOutput.minor_issues")
        require_list_of_str(payload["unsupported_claims"], "SkepticalReviewerOutput.unsupported_claims")
        require_list_of_str(payload["revision_instructions"], "SkepticalReviewerOutput.revision_instructions")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)
