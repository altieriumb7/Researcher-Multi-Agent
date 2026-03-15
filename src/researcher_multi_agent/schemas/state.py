from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class GoalProfile:
    user_goal: str
    constraints: list[str] = field(default_factory=list)

    def model_dump(self) -> dict:
        return asdict(self)


@dataclass
class SharedState:
    goal_profile: GoalProfile | None = None
    topic_pool: list[dict] = field(default_factory=list)
    reading_board: list[dict] = field(default_factory=list)
    project_board: list[dict] = field(default_factory=list)
    target_supervisors: list[dict] = field(default_factory=list)
    drafts: list[dict] = field(default_factory=list)
    review_log: list[dict] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
