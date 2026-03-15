from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from researcher_multi_agent.schemas.state import SharedState

T = TypeVar("T")


class BaseAgent(ABC, Generic[T]):
    name: str

    @abstractmethod
    def run(self, task: str, state: SharedState) -> T:
        """Execute agent task and return validated structured output."""


class DeterministicAgent(BaseAgent[T], ABC):
    """A deterministic local implementation used for orchestration/testing."""

    @abstractmethod
    def _build_payload(self, task: str, state: SharedState) -> dict:
        pass

    @property
    @abstractmethod
    def output_model(self):
        pass

    def run(self, task: str, state: SharedState) -> T:
        payload = self._build_payload(task=task, state=state)
        return self.output_model.model_validate(payload)
