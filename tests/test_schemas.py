import pytest

from researcher_multi_agent.schemas.agent_outputs import (
    ChiefOfStaffOutput,
    LiteratureCartographerOutput,
    ProjectArchitectOutput,
    SkepticalReviewerOutput,
)
from researcher_multi_agent.schemas.validation import SchemaValidationError


def test_chief_of_staff_schema_validation_passes() -> None:
    payload = {
        "goal_now": "Narrow topic",
        "assumptions": [],
        "delegations": [
            {
                "agent": "TopicStrategist",
                "task": "Do thing",
                "why_this_agent": "specialist",
                "priority": "high",
                "expected_output": "json",
            }
        ],
        "merged_plan": {"now": [], "parallel": [], "later": []},
        "risks": [],
        "state_update": {},
    }
    parsed = ChiefOfStaffOutput.model_validate(payload)
    assert parsed.delegations[0].priority == "high"


def test_chief_schema_rejects_invalid_delegation_priority() -> None:
    with pytest.raises(SchemaValidationError):
        ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "Narrow topic",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "TopicStrategist",
                        "task": "Do thing",
                        "why_this_agent": "specialist",
                        "priority": "urgent",
                        "expected_output": "json",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )


def test_reviewer_schema_rejects_invalid_verdict() -> None:
    with pytest.raises(SchemaValidationError):
        SkepticalReviewerOutput.model_validate(
            {
                "verdict": "MAYBE",
                "critical_issues": [],
                "minor_issues": [],
                "unsupported_claims": [],
                "revision_instructions": [],
                "confidence": "high",
            }
        )


def test_literature_cartographer_schema_validation_passes() -> None:
    parsed = LiteratureCartographerOutput.model_validate(
        {
            "topic": "Reasoning oversight",
            "clusters": [
                {
                    "cluster_name": "Failure detection",
                    "why_it_matters": "core",
                    "key_papers": ["Paper A"],
                    "benchmarks": ["GSM8K"],
                    "methods": ["probes"],
                    "open_disputes": ["transfer"],
                }
            ],
            "must_read": ["Paper A"],
            "optional_read": ["Paper B"],
            "benchmark_map": ["GSM8K: arithmetic"],
            "evidence_gaps": ["cross-model evidence"],
            "reading_ladder": [
                {"day": 1, "goal": "grounding", "papers": ["Paper A"], "notes_to_extract": ["metrics"]}
            ],
        }
    )
    assert parsed.clusters[0].cluster_name == "Failure detection"


def test_project_architect_schema_validation_passes() -> None:
    parsed = ProjectArchitectOutput.model_validate(
        {
            "project_title": "Probe project",
            "research_question": "RQ",
            "hypothesis": "H",
            "minimal_publishable_claim": "Claim",
            "datasets_tasks": ["GSM8K"],
            "baselines": ["entropy"],
            "method_outline": ["step 1"],
            "evaluation": {
                "primary_metrics": ["AUROC"],
                "secondary_metrics": ["ECE"],
                "ablations": ["feature groups"],
                "stress_tests": ["dataset shift"],
            },
            "resources": {
                "compute": "1 GPU",
                "data_needs": "traces",
                "engineering_needs": "pipeline",
            },
            "timeline": {
                "week_1_2": ["setup"],
                "week_3_4": ["baselines"],
                "week_5_8": ["experiments"],
            },
            "major_risks": ["risk"],
            "fallback_versions": ["fallback"],
        }
    )
    assert parsed.evaluation.primary_metrics == ["AUROC"]


def test_literature_cartographer_schema_rejects_empty_clusters() -> None:
    with pytest.raises(SchemaValidationError):
        LiteratureCartographerOutput.model_validate(
            {
                "topic": "Reasoning oversight",
                "clusters": [],
                "must_read": ["Paper A"],
                "optional_read": [],
                "benchmark_map": ["GSM8K"],
                "evidence_gaps": [],
                "reading_ladder": [
                    {"day": 1, "goal": "grounding", "papers": ["Paper A"], "notes_to_extract": ["metrics"]}
                ],
            }
        )


def test_project_architect_schema_rejects_missing_nested_fields() -> None:
    with pytest.raises(SchemaValidationError):
        ProjectArchitectOutput.model_validate(
            {
                "project_title": "Probe project",
                "research_question": "RQ",
                "hypothesis": "H",
                "minimal_publishable_claim": "Claim",
                "datasets_tasks": ["GSM8K"],
                "baselines": ["entropy"],
                "method_outline": ["step 1"],
                "evaluation": {
                    "primary_metrics": ["AUROC"],
                    "secondary_metrics": ["ECE"],
                    "ablations": ["feature groups"],
                },
                "resources": {
                    "compute": "1 GPU",
                    "data_needs": "traces",
                    "engineering_needs": "pipeline",
                },
                "timeline": {
                    "week_1_2": ["setup"],
                    "week_3_4": ["baselines"],
                    "week_5_8": ["experiments"],
                },
                "major_risks": ["risk"],
                "fallback_versions": ["fallback"],
            }
        )
