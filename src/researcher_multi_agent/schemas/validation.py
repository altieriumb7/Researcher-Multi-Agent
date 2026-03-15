from __future__ import annotations

from typing import Any


class SchemaValidationError(ValueError):
    pass


def require_fields(payload: dict[str, Any], required: list[str], schema_name: str) -> None:
    missing = [field for field in required if field not in payload]
    if missing:
        raise SchemaValidationError(f"{schema_name} missing fields: {missing}")


def require_literal(value: str, options: set[str], field_name: str) -> None:
    if value not in options:
        raise SchemaValidationError(f"{field_name} must be one of {sorted(options)}, got {value!r}")


def require_type(value: Any, expected_type: type | tuple[type, ...], field_name: str) -> None:
    if not isinstance(value, expected_type):
        raise SchemaValidationError(
            f"{field_name} must be of type {expected_type}, got {type(value)}"
        )


def require_list_of_str(value: Any, field_name: str) -> None:
    require_type(value, list, field_name)
    if not all(isinstance(item, str) for item in value):
        raise SchemaValidationError(f"{field_name} must contain only strings")


def require_int_range(value: Any, *, min_value: int, max_value: int, field_name: str) -> None:
    require_type(value, int, field_name)
    if value < min_value or value > max_value:
        raise SchemaValidationError(
            f"{field_name} must be in range [{min_value}, {max_value}], got {value}"
        )
