"""Partially observable PerceptaMaze game environment.

The agent receives only a description of its current room. The full graph is
kept inside the environment and is not included in observations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from .rules import RoomRule, rule_compliant_doors


class GameStatus(str, Enum):
    RUNNING = "running"
    WON = "won"
    LOST = "lost"


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
    is_dead_end: bool = False


@dataclass(frozen=True)
class Observation:
    """Information available to an agent at the current time."""

    room_id: str
    rule_text: str
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
    """Raised when an action refers to a door not visible in the room."""


class PerceptaMaze:
    """Maze game engine with rule compliance and no-backtracking enforcement."""

    def __init__(self, rooms: Mapping[str, Room], start_room: str, exit_room: str):
        if start_room not in rooms:
            raise ValueError(f"Unknown start room: {start_room}")
        if exit_room not in rooms:
            raise ValueError(f"Unknown exit room: {exit_room}")
        if not rooms[exit_room].is_exit:
            raise ValueError("The designated exit room must have is_exit=True")
        for room in rooms.values():
            if room.is_exit and room.is_dead_end:
                raise ValueError(f"Room {room.room_id} cannot be both exit and dead end")
            door_ids = [door.door_id for door in room.doors]
            if len(door_ids) != len(set(door_ids)):
                raise ValueError(f"Door IDs must be unique within room {room.room_id}")
            for door in room.doors:
                if door.destination not in rooms:
                    raise ValueError(
                        f"Door {door.door_id} in {room.room_id} points to unknown room "
                        f"{door.destination}"
                    )

        self._rooms = dict(rooms)
        self.start_room = start_room
        self.exit_room = exit_room
        self.current_room = start_room
        self.previous_room: str | None = None
        self.status = GameStatus.WON if self._rooms[start_room].is_exit else GameStatus.RUNNING
        self.history: list[str] = [start_room]

    def observe(self) -> Observation:
        """Return only current-room information, never the complete maze graph."""
        room = self._rooms[self.current_room]
        visible_doors = tuple(
            door for door in room.doors if door.destination != self.previous_room
        )
        return Observation(
            room_id=room.room_id,
            rule_text=room.rule.describe(),
            doors=visible_doors,
            previous_room=self.previous_room,
            status=self.status,
        )

    def step(self, door_id: str) -> StepResult:
        """Attempt a door choice, enforcing room rules and terminal outcomes."""
        if self.status is not GameStatus.RUNNING:
            raise RuntimeError(f"Game is already over: {self.status.value}")

        room = self._rooms[self.current_room]
        visible_doors = [
            door for door in room.doors if door.destination != self.previous_room
        ]
        compliant = rule_compliant_doors(visible_doors, room.rule)
        if not compliant:
            self.status = GameStatus.LOST
            return StepResult(
                status=self.status,
                message="No available door satisfies this room's rule. You lose.",
                entered_room=None,
                observation=self.observe(),
            )

        selected = next((door for door in visible_doors if door.door_id == door_id), None)
        if selected is None:
            raise InvalidMove(
                f"Door {door_id!r} is not available from room {self.current_room}; "
                "backtracking is forbidden."
            )
        if selected not in compliant:
            raise InvalidMove(f"Door {door_id!r} violates the instruction: {room.rule.describe()}")

        old_room = self.current_room
        self.previous_room = old_room
        self.current_room = selected.destination
        self.history.append(self.current_room)
        destination = self._rooms[self.current_room]

        if destination.is_dead_end:
            self.status = GameStatus.LOST
            message = f"Entered dead-end room {destination.room_id}. You lose immediately."
        elif destination.is_exit:
            self.status = GameStatus.WON
            message = "Exit reached. You win!"
        else:
            message = f"Moved from {old_room} to {destination.room_id}."

        return StepResult(
            status=self.status,
            message=message,
            entered_room=self.current_room,
            observation=self.observe(),
        )
