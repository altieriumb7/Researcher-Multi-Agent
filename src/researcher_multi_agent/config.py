from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ModelSettings:
    planner_model: str = "gpt-4.1-mini"
    specialist_model: str = "gpt-4.1-mini"
    reviewer_model: str = "gpt-4.1-mini"
    temperature: float = 0.2
    max_schema_repairs: int = 2


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str | None
    model_settings: ModelSettings


def load_config() -> AppConfig:
    """Load runtime config from environment variables."""
    return AppConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model_settings=ModelSettings(
            planner_model=os.getenv("PLANNER_MODEL", "gpt-4.1-mini"),
            specialist_model=os.getenv("SPECIALIST_MODEL", "gpt-4.1-mini"),
            reviewer_model=os.getenv("REVIEWER_MODEL", "gpt-4.1-mini"),
            temperature=float(os.getenv("MODEL_TEMPERATURE", "0.2")),
            max_schema_repairs=int(os.getenv("MAX_SCHEMA_REPAIRS", "2")),
        ),
    )
