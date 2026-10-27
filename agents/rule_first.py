"""Deterministic rule-first baseline agent."""

from __future__ import annotations

from agents.base_agent import BaseAgent, Decision
from maze.environment import Observation
from maze.rules import rule_compliant_doors


class RuleFirstAgent(BaseAgent):
    """Follow the room rule, then break ties by colour and door ID.

    Tie-break order: blue, green, red, then any other colours alphabetically;
    door IDs are the final deterministic tie-break. The agent receives only an
    Observation and has no reference to the environment's hidden room graph.
    """

    name = "Rule-first baseline"
    COLOR_PRIORITY = {"blue": 0, "green": 1, "red": 2}

    @classmethod
    def _sort_key(cls, door: object) -> tuple[int, str, str]:
        color = str(getattr(door, "color")).casefold()
        return (cls.COLOR_PRIORITY.get(color, 3), color, str(getattr(door, "door_id")))

    def choose_door(self, observation: Observation) -> Decision:
        if observation.status.value != "running":
            return Decision(
                door_id=None,
                reason=f"Game is already {observation.status.value}; no move selected.",
                considered_doors=(),
            )

        valid_doors = rule_compliant_doors(observation.doors, observation.rule)
        ordered = sorted(valid_doors, key=self._sort_key)
        considered = tuple(door.door_id for door in ordered)
        if not ordered:
            return Decision(
                door_id=None,
                reason="No visible door satisfies the room rule; the agent has no legal move.",
                considered_doors=(),
            )

        selected = ordered[0]
        return Decision(
            door_id=selected.door_id,
            reason=(
                f"Applied '{observation.rule_text}' and selected {selected.color} door "
                f"'{selected.door_id}' using the fixed tie-break order."
            ),
            considered_doors=considered,
        )
