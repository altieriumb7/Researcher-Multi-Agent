from pathlib import Path

import pytest

from researcher_multi_agent.agents.base import DeterministicAgent
from researcher_multi_agent.orchestrator.engine import OrchestrationEngine
from researcher_multi_agent.schemas.agent_outputs import (
    ChiefOfStaffOutput,
    NarrativeWriterOutput,
    ProjectArchitectOutput,
    SkepticalReviewerOutput,
    TopicStrategistOutput,
)
from researcher_multi_agent.schemas.state import GoalProfile, SharedState
from researcher_multi_agent.schemas.validation import SchemaValidationError
from researcher_multi_agent.utils.prompt_loader import PromptLoader


class BrokenPayloadAgent(DeterministicAgent[TopicStrategistOutput]):
    name = "BrokenPayload"

    @property
    def output_model(self) -> type[TopicStrategistOutput]:
        return TopicStrategistOutput

    def _build_payload(self, task: str, state: SharedState):
        return "not-a-dict"


class PartialPayloadAgent(DeterministicAgent[ProjectArchitectOutput]):
    name = "PartialPayload"

    @property
    def output_model(self) -> type[ProjectArchitectOutput]:
        return ProjectArchitectOutput

    def _build_payload(self, task: str, state: SharedState) -> dict:
        return {
            "project_title": "Incomplete project",
            "research_question": "RQ",
            "hypothesis": "H",
            "minimal_publishable_claim": "MPC",
            "datasets_tasks": ["dataset"],
            "baselines": ["baseline"],
            "method_outline": ["step"],
            "evaluation": {
                "primary_metrics": ["m1"],
                "secondary_metrics": ["m2"],
                "ablations": ["a"],
            },
            "resources": {
                "compute": "cpu",
                "data_needs": "small",
                "engineering_needs": "minimal",
            },
            "timeline": {
                "week_1_2": ["w1"],
                "week_3_4": ["w2"],
                "week_5_8": ["w3"],
            },
            "major_risks": ["risk"],
            "fallback_versions": ["fallback"],
        }


def test_deterministic_agent_rejects_non_dict_payload() -> None:
    agent = BrokenPayloadAgent()
    state = SharedState(goal_profile=GoalProfile(user_goal="goal"))

    with pytest.raises(SchemaValidationError):
        agent.run(task="anything", state=state)


def test_deterministic_agent_rejects_partial_payload() -> None:
    agent = PartialPayloadAgent()
    state = SharedState(goal_profile=GoalProfile(user_goal="goal"))

    with pytest.raises(SchemaValidationError):
        agent.run(task="build", state=state)


def test_prompt_loader_supports_explicit_directory(tmp_path: Path) -> None:
    prompt_dir = tmp_path / "prompts"
    prompt_dir.mkdir()
    (prompt_dir / "custom_agent.md").write_text("Custom prompt body", encoding="utf-8")

    loader = PromptLoader(prompts_dir=prompt_dir)
    loaded = loader.load("custom_agent")

    assert loaded == "Custom prompt body"


def test_prompt_loader_raises_for_missing_prompt(tmp_path: Path) -> None:
    loader = PromptLoader(prompts_dir=tmp_path)

    with pytest.raises(FileNotFoundError):
        loader.load("does_not_exist")


def test_review_revise_blocks_following_stages() -> None:
    engine = OrchestrationEngine()

    def fake_reviewer_run(task: str, state):
        if task.startswith("Review gate for LiteratureCartographer"):
            return SkepticalReviewerOutput.model_validate(
                {
                    "verdict": "REVISE",
                    "critical_issues": ["Need stronger benchmark coverage"],
                    "minor_issues": [],
                    "unsupported_claims": [],
                    "revision_instructions": ["Expand benchmark map"],
                    "confidence": "high",
                }
            )
        return SkepticalReviewerOutput.model_validate(
            {
                "verdict": "PASS",
                "critical_issues": [],
                "minor_issues": [],
                "unsupported_claims": [],
                "revision_instructions": [],
                "confidence": "medium",
            }
        )

    engine.reviewer.run = fake_reviewer_run  # type: ignore[method-assign]

    result = engine.run(goal="test revise loop")

    executed = [item["agent"] for item in result.state.timeline if item["event"] == "delegation_executed"]
    blocked = [item["agent"] for item in result.state.timeline if item["event"] == "delegation_blocked_by_review_gate"]

    assert executed == ["TopicStrategist", "LiteratureCartographer"]
    assert blocked == ["ProjectArchitect", "SupervisorMapper", "NarrativeWriter"]


def test_orchestration_surfaces_chief_schema_failure() -> None:
    engine = OrchestrationEngine()

    def fake_chief_run(task: str, state):
        return ChiefOfStaffOutput.model_validate(
            {
                "goal_now": "goal",
                "assumptions": [],
                "delegations": [
                    {
                        "agent": "TopicStrategist",
                        "task": "task",
                        "why_this_agent": "",
                        "priority": "invalid",
                        "expected_output": "",
                    }
                ],
                "merged_plan": {"now": [], "parallel": [], "later": []},
                "risks": [],
                "state_update": {},
            }
        )

    engine.chief.run = fake_chief_run  # type: ignore[method-assign]

    with pytest.raises(SchemaValidationError):
        engine.run(goal="break chief output")


def test_narrative_writer_output_schema_round_trip() -> None:
    payload = {
        "document_type": "supervisor_outreach_email",
        "target_audience": "Prof A",
        "tone": "warm",
        "drafts": [{"version_name": "v1", "text": "Hello Prof A"}],
        "customization_slots": ["recent paper", "method overlap"],
        "weak_sentences_to_avoid": ["I am passionate"],
        "evidence": [{"claim": "c", "source": "s", "confidence": "medium"}],
    }
    parsed = NarrativeWriterOutput.model_validate(payload)

    assert parsed.model_dump() == payload
