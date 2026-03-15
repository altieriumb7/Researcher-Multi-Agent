from __future__ import annotations


class SchemaValidationError(ValueError):
    pass


def require_fields(payload: dict, required: list[str], schema_name: str) -> None:
    missing = [field for field in required if field not in payload]
    if missing:
        raise SchemaValidationError(f"{schema_name} missing fields: {missing}")


def require_literal(value: str, options: set[str], field_name: str) -> None:
    if value not in options:
        raise SchemaValidationError(f"{field_name} must be one of {sorted(options)}, got {value!r}")
