from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from jsonschema import ValidationError as JSONSchemaValidationError
from jsonschema import validate
from openai import OpenAI

from researcher_multi_agent.schemas.validation import SchemaValidationError


@dataclass(frozen=True)
class LLMResult:
    raw_text: str
    parsed_json: dict[str, Any]


class LLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.2,
        max_repairs: int = 2,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_repairs = max_repairs
        self._client = OpenAI(api_key=api_key)

    def call_json_schema(self, system: str, user: str, json_schema: dict[str, Any]) -> LLMResult:
        response = self._client.responses.create(
            model=self.model,
            temperature=self.temperature,
            input=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "agent_output",
                    "schema": json_schema,
                    "strict": True,
                }
            },
        )
        raw_text = self._extract_raw_text(response)
        try:
            parsed = self._parse_and_validate(raw_text=raw_text, json_schema=json_schema)
            return LLMResult(raw_text=raw_text, parsed_json=parsed)
        except SchemaValidationError:
            return self._repair_invalid_output(
                invalid_output=raw_text,
                json_schema=json_schema,
                system_prompt=system,
                user_prompt=user,
            )

    def _repair_invalid_output(
        self,
        invalid_output: str,
        json_schema: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResult:
        latest_raw = invalid_output
        for attempt in range(1, self.max_repairs + 1):
            repair_response = self._client.responses.create(
                model=self.model,
                temperature=0,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You repair malformed model outputs. Return only valid JSON that matches "
                            "the provided schema exactly."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Original system prompt:\n{system_prompt}\n\n"
                            f"Original user prompt:\n{user_prompt}\n\n"
                            f"JSON schema:\n{json.dumps(json_schema)}\n\n"
                            f"Invalid output:\n{latest_raw}\n\n"
                            "Respond with ONLY repaired JSON."
                        ),
                    },
                ],
            )
            latest_raw = self._extract_raw_text(repair_response)
            try:
                parsed = self._parse_and_validate(raw_text=latest_raw, json_schema=json_schema)
                return LLMResult(raw_text=latest_raw, parsed_json=parsed)
            except SchemaValidationError:
                if attempt == self.max_repairs:
                    raise

        raise SchemaValidationError("Schema repair loop ended without valid JSON output")

    def _extract_raw_text(self, response: Any) -> str:
        if hasattr(response, "output_text") and response.output_text:
            return str(response.output_text)

        output = getattr(response, "output", None) or []
        text_chunks: list[str] = []
        for item in output:
            content = getattr(item, "content", None) or []
            for block in content:
                text = getattr(block, "text", None)
                if text:
                    text_chunks.append(text)
        if text_chunks:
            return "\n".join(text_chunks)

        raise SchemaValidationError("LLM response did not contain textual output")

    def _parse_and_validate(self, raw_text: str, json_schema: dict[str, Any]) -> dict[str, Any]:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise SchemaValidationError(f"Model output is not valid JSON: {exc}") from exc

        if not isinstance(parsed, dict):
            raise SchemaValidationError("Model output must be a JSON object")

        try:
            validate(instance=parsed, schema=json_schema)
        except JSONSchemaValidationError as exc:
            raise SchemaValidationError(f"Model output failed schema validation: {exc.message}") from exc

        return parsed
