from __future__ import annotations

import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

try:
    import gradio as gr
except ModuleNotFoundError as exc:  # pragma: no cover - import guard for local setup clarity
    raise RuntimeError(
        "Gradio is required to run this app. Install dependencies with: pip install -r requirements.txt"
    ) from exc

REPO_ROOT = Path(__file__).resolve().parent
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from researcher_multi_agent.orchestrator.engine import OrchestrationEngine


def parse_constraints(raw_constraints: str) -> list[str]:
    """Parse constraints from newline and/or comma-separated text safely."""
    if not raw_constraints or not raw_constraints.strip():
        return []

    parts: list[str] = []
    for line in raw_constraints.splitlines():
        for chunk in line.split(","):
            cleaned = chunk.strip()
            if cleaned:
                parts.append(cleaned)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in parts:
        normalized = item.casefold()
        if normalized not in seen:
            seen.add(normalized)
            deduped.append(item)

    return deduped


def format_summary(result: Any) -> str:
    recommended_focus = []
    if result.topic_strategist is not None:
        recommended_focus = result.topic_strategist.recommended_focus

    executed_count = len([event for event in result.state.timeline if event.get("event") == "delegation_executed"])
    lines = [
        "### Final Summary",
        f"- **Goal now:** {result.chief_of_staff.goal_now}",
        f"- **Delegated stages executed:** {executed_count}",
        f"- **Final reviewer verdict:** {result.skeptical_reviewer.verdict}",
    ]

    if recommended_focus:
        lines.append("- **Recommended focus:** " + "; ".join(recommended_focus))

    return "\n".join(lines)


def format_timeline(result: Any) -> str:
    if not result.state.timeline:
        return "_No timeline events were recorded._"

    lines = ["### Timeline / Major Steps"]
    for idx, event in enumerate(result.state.timeline, start=1):
        event_name = event.get("event", "unknown_event")
        details = ", ".join(f"{key}={value}" for key, value in event.items() if key != "event")
        if details:
            lines.append(f"{idx}. **{event_name}** — {details}")
        else:
            lines.append(f"{idx}. **{event_name}**")

    return "\n".join(lines)


def format_reviewer_output(result: Any) -> str:
    reviewer = result.skeptical_reviewer
    lines = [
        "### Skeptical Reviewer Output",
        f"- **Verdict:** {reviewer.verdict}",
        f"- **Confidence:** {reviewer.confidence}",
    ]

    if reviewer.critical_issues:
        lines.append("- **Critical issues:**")
        lines.extend([f"  - {issue}" for issue in reviewer.critical_issues])

    if reviewer.minor_issues:
        lines.append("- **Minor issues:**")
        lines.extend([f"  - {issue}" for issue in reviewer.minor_issues])

    if reviewer.revision_instructions:
        lines.append("- **Revision instructions:**")
        lines.extend([f"  - {item}" for item in reviewer.revision_instructions])

    return "\n".join(lines)


def serialize_result(result: Any) -> dict[str, Any]:
    return {
        "chief_of_staff": result.chief_of_staff.model_dump(),
        "topic_strategist": result.topic_strategist.model_dump() if result.topic_strategist else None,
        "literature_cartographer": result.literature_cartographer.model_dump()
        if result.literature_cartographer
        else None,
        "project_architect": result.project_architect.model_dump() if result.project_architect else None,
        "supervisor_mapper": result.supervisor_mapper.model_dump() if result.supervisor_mapper else None,
        "narrative_writer": result.narrative_writer.model_dump() if result.narrative_writer else None,
        "skeptical_reviewer": result.skeptical_reviewer.model_dump(),
        "state": asdict(result.state),
    }


def run_system(goal: str, raw_constraints: str, progress: gr.Progress = gr.Progress()):
    if not goal or not goal.strip():
        raise gr.Error("Please enter a goal before running the multi-agent system.")

    if not os.getenv("OPENAI_API_KEY"):
        raise gr.Error(
            "OPENAI_API_KEY is not set. Add it in your environment (or Hugging Face Space Secrets) and try again."
        )

    constraints = parse_constraints(raw_constraints)

    try:
        progress(0.15, desc="Initializing orchestration engine...")
        engine = OrchestrationEngine()

        progress(0.75, desc="Running manager-led multi-agent workflow...")
        result = engine.run(goal=goal.strip(), constraints=constraints)

        progress(1.0, desc="Formatting outputs...")
        return (
            "✅ Run completed successfully.",
            format_summary(result),
            format_timeline(result),
            format_reviewer_output(result),
            serialize_result(result),
        )
    except Exception as exc:
        raise gr.Error(f"The orchestration engine failed: {type(exc).__name__}: {exc}") from exc


def clear_all() -> tuple[str, str, str, str, str, dict[str, Any] | None]:
    return "", "", "", "", "", None


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Researcher Multi-Agent Space") as demo:
        gr.Markdown("# Researcher Multi-Agent")
        gr.Markdown(
            "Run a manager-led multi-agent research planning workflow from your browser. "
            "Enter a goal, optionally add constraints, and inspect readable outputs plus raw JSON."
        )

        goal_input = gr.Textbox(
            label="User Goal",
            lines=8,
            placeholder="Describe your research or planning goal...",
        )

        constraints_input = gr.Textbox(
            label="Constraints (optional)",
            lines=4,
            placeholder="One per line or comma-separated (e.g., no wet lab, finish in 8 weeks, low compute budget)",
        )

        with gr.Row():
            run_button = gr.Button("Run", variant="primary")
            clear_button = gr.Button("Clear")

        status_output = gr.Markdown("_Ready. Enter a goal and click **Run**._")
        summary_output = gr.Markdown()
        timeline_output = gr.Markdown()
        reviewer_output = gr.Markdown()

        with gr.Accordion("Raw Structured Result (JSON)", open=False):
            raw_output = gr.JSON(label="Raw Result")

        run_button.click(
            fn=run_system,
            inputs=[goal_input, constraints_input],
            outputs=[status_output, summary_output, timeline_output, reviewer_output, raw_output],
        )
        clear_button.click(
            fn=clear_all,
            inputs=None,
            outputs=[goal_input, constraints_input, status_output, summary_output, timeline_output, reviewer_output],
        ).then(
            fn=lambda: None,
            inputs=None,
            outputs=raw_output,
        )

    return demo


demo = build_app()


if __name__ == "__main__":
    demo.queue().launch()
