from researcher_multi_agent.agents.narrative_writer import NarrativeWriter
from researcher_multi_agent.agents.supervisor_mapper import SupervisorMapper
from researcher_multi_agent.orchestrator.engine import OrchestrationEngine
from researcher_multi_agent.schemas.state import GoalProfile, SharedState
from researcher_multi_agent.utils.prompt_loader import PromptLoader


def test_supervisor_mapper_returns_ranked_targets() -> None:
    state = SharedState(goal_profile=GoalProfile(user_goal="goal"), project_board=[{"project_title": "Project X"}])
    agent = SupervisorMapper(PromptLoader())

    output = agent.run(task="Rank targets", state=state)

    priorities = [target.priority for target in output.targets]
    assert priorities == sorted(priorities)
    assert output.targets[0].fit_level == "primary"


def test_narrative_writer_generates_outreach_draft_from_targets() -> None:
    state = SharedState(
        goal_profile=GoalProfile(user_goal="goal"),
        target_supervisors=[
            {
                "targets": [
                    {
                        "name": "Supervisor A",
                        "institution": "University Alpha",
                    }
                ]
            }
        ],
    )
    agent = NarrativeWriter(PromptLoader())

    output = agent.run(task="Write outreach", state=state)

    assert output.document_type == "supervisor_outreach_email"
    assert output.drafts
    assert "Supervisor A" in output.drafts[0].text


def test_orchestrator_milestone4_chain_produces_targets_and_drafts() -> None:
    engine = OrchestrationEngine()
    result = engine.run(goal="Find supervision targets and draft outreach")

    assert result.supervisor_mapper is not None
    assert result.narrative_writer is not None
    assert result.state.target_supervisors
    assert result.state.drafts
