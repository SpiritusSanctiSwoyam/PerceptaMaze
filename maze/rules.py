"""Room rules for PerceptaMaze's perception-based branching maze."""
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class RuleKind(str, Enum):
    CHOOSE = "choose"
    AVOID = "avoid"


@dataclass(frozen=True)
class RoomRule:
    kind: RuleKind
    color: str

    def allows(self, door_color: str) -> bool:
        match = door_color.casefold() == self.color.casefold()
        return match if self.kind is RuleKind.CHOOSE else not match

    def describe(self) -> str:
        return f"{'Choose' if self.kind is RuleKind.CHOOSE else 'Avoid'} {self.color.upper()}"


def rule_compliant_doors(doors: Iterable[object], rule: RoomRule) -> list[object]:
    return [door for door in doors if rule.allows(getattr(door, "color"))]
