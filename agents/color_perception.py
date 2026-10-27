"""Configurable simulated colour perception for PerceptaMaze.

This is a deliberately simplified game model, not a clinical simulation of
colour vision deficiency. In the default mode, red and green labels become
indistinguishable to the agent while blue remains distinct.
"""

from __future__ import annotations

from dataclasses import replace
from enum import Enum

from maze.environment import Observation
from maze.rules import RoomRule


class PerceptionMode(str, Enum):
    NORMAL = "normal"
    RED_GREEN_AMBIGUOUS = "red_green_ambiguous"


class ColorPerceptionModel:
    """Transform an observation into the colours perceived by an agent.

    Door IDs, destinations, room IDs, previous-room information, and game
    status are preserved. Only visible door-colour labels and the rule's target
    colour are transformed. No hidden environment state is accepted or read.
    """

    def __init__(self, mode: PerceptionMode = PerceptionMode.RED_GREEN_AMBIGUOUS):
        self.mode = PerceptionMode(mode)

    def perceive_color(self, color: str) -> str:
        normalized = color.casefold()
        if self.mode is PerceptionMode.NORMAL:
            return normalized
        if normalized in {"red", "green"}:
            return "red-green ambiguous"
        return normalized

    def transform(self, observation: Observation) -> Observation:
        """Return a transformed copy without mutating the real observation."""
        if self.mode is PerceptionMode.NORMAL:
            return observation

        perceived_doors = tuple(
            replace(door, color=self.perceive_color(door.color))
            for door in observation.doors
        )
        perceived_rule = RoomRule(
            kind=observation.rule.kind,
            color=self.perceive_color(observation.rule.color),
        )
        return replace(
            observation,
            rule=perceived_rule,
            rule_text=perceived_rule.describe(),
            doors=perceived_doors,
        )
