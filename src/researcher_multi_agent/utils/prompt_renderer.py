from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any


GLOBAL_RULES_PLACEHOLDER = "{{GLOBAL_RULES}}"
DELIVERABLES_PLACEHOLDER = "{{DELIVERABLES_CONTRACT}}"
STATE_SUMMARY_PLACEHOLDER = "{{STATE_SUMMARY}}"


def render_prompt(
    template: str,
    global_rules: str,
    deliverables_contract: Mapping[str, Any] | None = None,
    state_summary: Mapping[str, Any] | None = None,
) -> str:
    rendered = template.replace(GLOBAL_RULES_PLACEHOLDER, global_rules.strip())

    if DELIVERABLES_PLACEHOLDER in rendered:
        rendered = rendered.replace(
            DELIVERABLES_PLACEHOLDER,
            _format_section("Deliverables Contract", deliverables_contract),
        )

    if STATE_SUMMARY_PLACEHOLDER in rendered:
        rendered = rendered.replace(
            STATE_SUMMARY_PLACEHOLDER,
            _format_section("Concise State Summary", state_summary),
        )

    return rendered


def _format_section(title: str, payload: Mapping[str, Any] | None) -> str:
    if not payload:
        return f"{title}: not provided."

    serialized_payload = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
    return f"{title}:\n{serialized_payload}"
