import pytest

from researcher_multi_agent.schemas.agent_outputs import (
    ChiefOfStaffOutput,
    SkepticalReviewerOutput,
    TopicStrategistOutput,
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


def test_topic_schema_rejects_invalid_scorecard_shape() -> None:
    with pytest.raises(SchemaValidationError):
        TopicStrategistOutput.model_validate(
            {
                "candidate_directions": [
                    {
                        "name": "x",
                        "problem_statement": "y",
                        "core_hypothesis": "z",
                        "scorecard": {"bottleneck_value": 6},
                        "why_promising": [],
                        "why_risky": [],
                        "kill_criteria": [],
                        "first_paper_angle": "a",
                    }
                ],
                "recommended_focus": ["x"],
                "decisive_next_questions": ["q"],
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
