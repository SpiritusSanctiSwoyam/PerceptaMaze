"""Explicit room-rule definitions and rule evaluation."""

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RuleKind(str, Enum):
    CHOOSE = "choose"
    AVOID = "avoid"


@dataclass(frozen=True)
class RoomRule:
    """A room instruction: choose a colour, or avoid a colour."""

    kind: RuleKind
    color: str

    def allows(self, door_color: str) -> bool:
        color = door_color.casefold()
        target = self.color.casefold()
        if self.kind is RuleKind.CHOOSE:
            return color == target
        return color != target

    def describe(self) -> str:
        verb = "Choose" if self.kind is RuleKind.CHOOSE else "Do not choose"
        return f"{verb} {self.color}."


def rule_compliant_doors(doors: Iterable[object], rule: RoomRule) -> list[object]:
    """Return doors whose colour satisfies ``rule``; preserves input order."""
    return [door for door in doors if rule.allows(getattr(door, "color"))]
