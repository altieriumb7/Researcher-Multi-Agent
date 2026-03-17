from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from researcher_multi_agent.agents.base import BaseAgent
from researcher_multi_agent.schemas.state import SharedState

T = TypeVar("T")


class LLMAgent(BaseAgent[T], ABC, Generic[T]):
    """Reusable base for OpenAI-backed agents with strict JSON schema outputs."""

    def __init__(self, llm_client: Any, prompt: str) -> None:
        self.llm_client = llm_client
        self.prompt = prompt

    @property
    @abstractmethod
    def output_model(self):
        pass

    @property
    @abstractmethod
    def output_schema(self) -> dict:
        pass

    @abstractmethod
    def build_user_prompt(self, task: str, state: SharedState) -> str:
        pass

    def run(self, task: str, state: SharedState) -> T:
        result = self.llm_client.call_json_schema(
            system=self.prompt,
            user=self.build_user_prompt(task=task, state=state),
            json_schema=self.output_schema,
        )
        return self.output_model.model_validate(result.parsed_json)
