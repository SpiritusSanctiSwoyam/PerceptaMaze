"""Partially observable, rooted-tree PerceptaMaze environment."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Mapping
from .rules import RoomRule, RuleKind, rule_compliant_doors


class GameStatus(str, Enum):
    RUNNING = "running"
    WON = "won"                 # Gold exit reached; the only winning condition.
    EXITED = "ordinary_exit"    # Escaped without Gold; episode ends, not a win.
    LOST = "lost"               # Reserved for invalid/failed game states.


@dataclass(frozen=True)
class Door:
    door_id: str
    color: str
    destination: str


@dataclass(frozen=True)
class Room:
    room_id: str
    rule: RoomRule
    doors: tuple[Door, ...]
    is_exit: bool = False
    is_dead_end: bool = False  # Kept for backwards-compatible test fixtures.
    is_gold_exit: bool = False
    red_green_equivalence: bool = False


@dataclass(frozen=True)
class Observation:
    room_id: str
    rule_text: str
    rule: RoomRule
    doors: tuple[Door, ...]
    previous_room: str | None
    status: GameStatus


@dataclass(frozen=True)
class StepResult:
    status: GameStatus
    message: str
    entered_room: str | None
    observation: Observation


class InvalidMove(ValueError):
    pass


class PerceptaMaze:
    """Environment owns the full tree; observations reveal only the current room."""
    def __init__(self, rooms: Mapping[str, Room], start_room: str, exit_room: str | None = None):
        if start_room not in rooms:
            raise ValueError(f"Unknown start room: {start_room}")
        gold_rooms = [rid for rid, room in rooms.items() if room.is_gold_exit]
        if len(gold_rooms) > 1:
            raise ValueError("A maze must contain at most one Gold exit")
        if exit_room is not None and exit_room not in rooms:
            raise ValueError(f"Unknown exit room: {exit_room}")
        self._rooms = dict(rooms)
        self.start_room = start_room
        self.gold_room = gold_rooms[0] if gold_rooms else exit_room
        self.exit_room = self.gold_room
        self.current_room = start_room
        self.previous_room: str | None = None
        self.status = GameStatus.WON if self._rooms[start_room].is_gold_exit else (GameStatus.EXITED if self._rooms[start_room].is_exit else GameStatus.RUNNING)
        self.history: list[str] = [start_room]
        for room in self._rooms.values():
            ids = [door.door_id for door in room.doors]
            if len(ids) != len(set(ids)):
                raise ValueError(f"Door IDs must be unique in room {room.room_id}")
            for door in room.doors:
                if door.destination not in self._rooms:
                    raise ValueError(f"Unknown destination {door.destination!r} in {room.room_id}")
            if room.is_gold_exit and not room.is_exit:
                raise ValueError("Gold exit must also be an exit")
            if room.is_exit and room.doors:
                raise ValueError(f"Terminal exit {room.room_id} cannot have outgoing doors")
            if room.doors and len(room.doors) != 3:
                raise ValueError(f"Decision room {room.room_id} must have exactly three doors")

    def observe(self) -> Observation:
        room = self._rooms[self.current_room]
        # Tree maze has no back edges, but retain the previous-room filter defensively.
        doors = tuple(d for d in room.doors if d.destination != self.previous_room)
        return Observation(room.room_id, room.rule.describe(), room.rule, doors, self.previous_room, self.status)

    def step(self, door_id: str) -> StepResult:
        if self.status is not GameStatus.RUNNING:
            raise RuntimeError(f"Game is already over: {self.status.value}")
        room = self._rooms[self.current_room]
        visible = [d for d in room.doors if d.destination != self.previous_room]
        selected = next((d for d in visible if d.door_id == door_id), None)
        if selected is None:
            raise InvalidMove(f"Door {door_id!r} is not available in room {self.current_room}")
        compliant = rule_compliant_doors(visible, room.rule)
        equivalent = (
            room.red_green_equivalence
            and room.rule.kind is RuleKind.CHOOSE
            and room.rule.color.casefold() in {"red", "green"}
            and selected.color.casefold() in {"red", "green"}
        )
        # If a CHOOSE target is absent, the room deliberately permits fallback choices.
        # In equivalence rooms, the red/green counterpart is a correct game answer.
        if compliant and selected not in compliant and not equivalent:
            raise InvalidMove(f"Door {door_id!r} violates the instruction: {room.rule.describe()}")
        old = self.current_room
        self.previous_room = old
        self.current_room = selected.destination
        self.history.append(self.current_room)
        destination = self._rooms[self.current_room]
        if destination.is_gold_exit:
            self.status = GameStatus.WON
            message = "🏆 GOLD FOUND! You win PerceptaMaze."
        elif destination.is_exit:
            self.status = GameStatus.EXITED
            message = "Ordinary exit reached. You escaped, but did not find Gold."
        elif destination.is_dead_end:
            self.status = GameStatus.EXITED
            message = "You reached a non-Gold terminal route. Try another attempt to find Gold."
        else:
            message = f"Moved from {old} to {destination.room_id}."
        return StepResult(self.status, message, self.current_room, self.observe())
