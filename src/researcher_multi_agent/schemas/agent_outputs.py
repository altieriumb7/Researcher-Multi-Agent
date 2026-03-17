from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from researcher_multi_agent.schemas.validation import (
    SchemaValidationError,
    require_fields,
    require_literal,
)


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
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoalDeliverables:
    must_include: list[str]
    nice_to_have: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GoalDeliverables":
        require_fields(payload, ["must_include", "nice_to_have"], "GoalDeliverables")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GoalIntentOutput:
    mode: str
    deliverables: GoalDeliverables
    success_criteria: list[str]
    questions_to_user_optional: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "GoalIntentOutput":
        require_fields(payload, ["mode", "deliverables", "success_criteria", "assumptions"], "GoalIntentOutput")
        require_literal(payload["mode"], {"MAP", "NARROW"}, "GoalIntentOutput.mode")
        questions = payload.get("questions_to_user_optional", [])
        if not isinstance(questions, list):
            raise SchemaValidationError("GoalIntentOutput.questions_to_user_optional must be a list")
        return cls(
            mode=payload["mode"],
            deliverables=GoalDeliverables.from_dict(payload["deliverables"]),
            success_criteria=payload["success_criteria"],
            questions_to_user_optional=questions,
            assumptions=payload["assumptions"],
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "deliverables": self.deliverables.model_dump(),
            "success_criteria": self.success_criteria,
            "questions_to_user_optional": self.questions_to_user_optional,
            "assumptions": self.assumptions,
        }


@dataclass
class MergedPlan:
    now: list[str]
    parallel: list[str]
    later: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MergedPlan":
        require_fields(payload, ["now", "parallel", "later"], "MergedPlan")
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
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LiteratureCluster:
    cluster_name: str
    why_it_matters: str
    key_papers: list[str]
    benchmarks: list[str]
    methods: list[str]
    open_disputes: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LiteratureCluster":
        require_fields(
            payload,
            ["cluster_name", "why_it_matters", "key_papers", "benchmarks", "methods", "open_disputes"],
            "LiteratureCluster",
        )
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReadingLadderStep:
    day: int
    goal: str
    papers: list[str]
    notes_to_extract: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ReadingLadderStep":
        require_fields(payload, ["day", "goal", "papers", "notes_to_extract"], "ReadingLadderStep")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LiteratureCartographerOutput:
    topic: str
    clusters: list[LiteratureCluster]
    must_read: list[str]
    optional_read: list[str]
    benchmark_map: list[str]
    evidence_gaps: list[str]
    reading_ladder: list[ReadingLadderStep]

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "LiteratureCartographerOutput":
        require_fields(
            payload,
            ["topic", "clusters", "must_read", "optional_read", "benchmark_map", "evidence_gaps", "reading_ladder"],
            "LiteratureCartographerOutput",
        )
        clusters = [LiteratureCluster.from_dict(item) for item in payload["clusters"]]
        reading_ladder = [ReadingLadderStep.from_dict(item) for item in payload["reading_ladder"]]
        if not clusters:
            raise SchemaValidationError("LiteratureCartographerOutput requires at least one cluster")
        if not reading_ladder:
            raise SchemaValidationError("LiteratureCartographerOutput requires a reading ladder")
        return cls(
            topic=payload["topic"],
            clusters=clusters,
            must_read=payload["must_read"],
            optional_read=payload["optional_read"],
            benchmark_map=payload["benchmark_map"],
            evidence_gaps=payload["evidence_gaps"],
            reading_ladder=reading_ladder,
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "clusters": [cluster.model_dump() for cluster in self.clusters],
            "must_read": self.must_read,
            "optional_read": self.optional_read,
            "benchmark_map": self.benchmark_map,
            "evidence_gaps": self.evidence_gaps,
            "reading_ladder": [step.model_dump() for step in self.reading_ladder],
        }


@dataclass
class ProjectEvaluation:
    primary_metrics: list[str]
    secondary_metrics: list[str]
    ablations: list[str]
    stress_tests: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectEvaluation":
        require_fields(
            payload,
            ["primary_metrics", "secondary_metrics", "ablations", "stress_tests"],
            "ProjectEvaluation",
        )
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectResources:
    compute: str
    data_needs: str
    engineering_needs: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectResources":
        require_fields(payload, ["compute", "data_needs", "engineering_needs"], "ProjectResources")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectTimeline:
    week_1_2: list[str]
    week_3_4: list[str]
    week_5_8: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ProjectTimeline":
        require_fields(payload, ["week_1_2", "week_3_4", "week_5_8"], "ProjectTimeline")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProjectArchitectOutput:
    project_title: str
    research_question: str
    hypothesis: str
    minimal_publishable_claim: str
    datasets_tasks: list[str]
    baselines: list[str]
    method_outline: list[str]
    evaluation: ProjectEvaluation
    resources: ProjectResources
    timeline: ProjectTimeline
    major_risks: list[str]
    fallback_versions: list[str]

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "ProjectArchitectOutput":
        require_fields(
            payload,
            [
                "project_title",
                "research_question",
                "hypothesis",
                "minimal_publishable_claim",
                "datasets_tasks",
                "baselines",
                "method_outline",
                "evaluation",
                "resources",
                "timeline",
                "major_risks",
                "fallback_versions",
            ],
            "ProjectArchitectOutput",
        )
        return cls(
            project_title=payload["project_title"],
            research_question=payload["research_question"],
            hypothesis=payload["hypothesis"],
            minimal_publishable_claim=payload["minimal_publishable_claim"],
            datasets_tasks=payload["datasets_tasks"],
            baselines=payload["baselines"],
            method_outline=payload["method_outline"],
            evaluation=ProjectEvaluation.from_dict(payload["evaluation"]),
            resources=ProjectResources.from_dict(payload["resources"]),
            timeline=ProjectTimeline.from_dict(payload["timeline"]),
            major_risks=payload["major_risks"],
            fallback_versions=payload["fallback_versions"],
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "project_title": self.project_title,
            "research_question": self.research_question,
            "hypothesis": self.hypothesis,
            "minimal_publishable_claim": self.minimal_publishable_claim,
            "datasets_tasks": self.datasets_tasks,
            "baselines": self.baselines,
            "method_outline": self.method_outline,
            "evaluation": self.evaluation.model_dump(),
            "resources": self.resources.model_dump(),
            "timeline": self.timeline.model_dump(),
            "major_risks": self.major_risks,
            "fallback_versions": self.fallback_versions,
        }


@dataclass
class SupervisorTarget:
    name: str
    institution: str
    fit_level: str
    fit_reasons: list[str]
    relevant_themes_to_mention: list[str]
    best_outreach_angle: str
    risks_or_red_flags: list[str]
    priority: int

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SupervisorTarget":
        require_fields(
            payload,
            [
                "name",
                "institution",
                "fit_level",
                "fit_reasons",
                "relevant_themes_to_mention",
                "best_outreach_angle",
                "risks_or_red_flags",
                "priority",
            ],
            "SupervisorTarget",
        )
        require_literal(
            payload["fit_level"],
            {"primary", "adjacent", "opportunistic"},
            "SupervisorTarget.fit_level",
        )
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SupervisorSegmentation:
    reach: list[str]
    strong_fit: list[str]
    safe_fit: list[str]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SupervisorSegmentation":
        require_fields(payload, ["reach", "strong_fit", "safe_fit"], "SupervisorSegmentation")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SupervisorMapperOutput:
    targets: list[SupervisorTarget]
    segmentation: SupervisorSegmentation

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "SupervisorMapperOutput":
        require_fields(payload, ["targets", "segmentation"], "SupervisorMapperOutput")
        targets = [SupervisorTarget.from_dict(item) for item in payload["targets"]]
        if not targets:
            raise SchemaValidationError("SupervisorMapperOutput requires at least one target")

        priorities = [target.priority for target in targets]
        if priorities != sorted(priorities):
            raise SchemaValidationError("SupervisorMapperOutput priorities must be sorted ascending")
        if len(priorities) != len(set(priorities)):
            raise SchemaValidationError("SupervisorMapperOutput priorities must be unique")

        target_names = {target.name for target in targets}
        segmentation = SupervisorSegmentation.from_dict(payload["segmentation"])
        segmented_names = segmentation.reach + segmentation.strong_fit + segmentation.safe_fit
        if any(name not in target_names for name in segmented_names):
            raise SchemaValidationError("SupervisorMapperOutput segmentation includes unknown target name")

        return cls(
            targets=targets,
            segmentation=segmentation,
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "targets": [target.model_dump() for target in self.targets],
            "segmentation": self.segmentation.model_dump(),
        }


@dataclass
class NarrativeDraft:
    version_name: str
    text: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "NarrativeDraft":
        require_fields(payload, ["version_name", "text"], "NarrativeDraft")
        return cls(**payload)

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class NarrativeWriterOutput:
    document_type: str
    target_audience: str
    tone: str
    drafts: list[NarrativeDraft]
    customization_slots: list[str]
    weak_sentences_to_avoid: list[str]

    @classmethod
    def model_validate(cls, payload: dict[str, Any]) -> "NarrativeWriterOutput":
        require_fields(
            payload,
            [
                "document_type",
                "target_audience",
                "tone",
                "drafts",
                "customization_slots",
                "weak_sentences_to_avoid",
            ],
            "NarrativeWriterOutput",
        )
        drafts = [NarrativeDraft.from_dict(item) for item in payload["drafts"]]
        if not drafts:
            raise SchemaValidationError("NarrativeWriterOutput requires at least one draft")
        if any(not draft.text.strip() for draft in drafts):
            raise SchemaValidationError("NarrativeWriterOutput draft text must be non-empty")
        return cls(
            document_type=payload["document_type"],
            target_audience=payload["target_audience"],
            tone=payload["tone"],
            drafts=drafts,
            customization_slots=payload["customization_slots"],
            weak_sentences_to_avoid=payload["weak_sentences_to_avoid"],
        )

    def model_dump(self) -> dict[str, Any]:
        return {
            "document_type": self.document_type,
            "target_audience": self.target_audience,
            "tone": self.tone,
            "drafts": [draft.model_dump() for draft in self.drafts],
            "customization_slots": self.customization_slots,
            "weak_sentences_to_avoid": self.weak_sentences_to_avoid,
        }
