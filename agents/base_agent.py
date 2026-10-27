"""Shared decision types for PerceptaMaze agents."""

from dataclasses import dataclass

from maze.environment import Observation


@dataclass(frozen=True)
class Decision:
    """A decision made from an observation, without access to the hidden maze."""

    door_id: str | None
    reason: str
    considered_doors: tuple[str, ...]

    @property
    def has_move(self) -> bool:
        return self.door_id is not None


class BaseAgent:
    """Interface implemented by agents that act only on current observations."""

    name = "BaseAgent"

    def choose_door(self, observation: Observation) -> Decision:
        raise NotImplementedError
