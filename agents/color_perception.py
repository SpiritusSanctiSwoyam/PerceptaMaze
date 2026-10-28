"""Simplified red-green ambiguity model used by the game."""
from __future__ import annotations
from dataclasses import replace
from enum import Enum
from maze.environment import Observation
from maze.rules import RoomRule


class PerceptionMode(str, Enum):
    NORMAL = "normal"
    RED_GREEN_AMBIGUOUS = "red_green_ambiguous"


class ColorPerceptionModel:
    def __init__(self, mode: PerceptionMode = PerceptionMode.RED_GREEN_AMBIGUOUS):
        self.mode = PerceptionMode(mode)

    def perceive_color(self, color: str) -> str:
        color = color.casefold()
        if self.mode is PerceptionMode.RED_GREEN_AMBIGUOUS and color in {"red", "green"}:
            return "red-green ambiguous"
        return color

    def transform(self, observation: Observation) -> Observation:
        if self.mode is PerceptionMode.NORMAL:
            return observation
        # Preserve the printed instruction for the player, but transform its internal
        # target category in the agent observation just as the doors are transformed.
        perceived_doors = tuple(replace(d, color=self.perceive_color(d.color)) for d in observation.doors)
        perceived_rule = RoomRule(observation.rule.kind, self.perceive_color(observation.rule.color))
        return replace(observation, rule=perceived_rule, doors=perceived_doors)
