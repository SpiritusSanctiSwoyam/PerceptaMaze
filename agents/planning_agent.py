"""Memory-based exploration planner for the partially observable maze.

The planner never receives the environment or its hidden room graph. It stores
only observations it has actually received and uses that discovered graph to
prefer unexplored, rule-compliant destinations.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from agents.base_agent import BaseAgent, Decision
from maze.environment import Observation
from maze.rules import RoomRule, rule_compliant_doors


@dataclass
class _KnownRoom:
    rule: RoomRule
    doors: tuple[tuple[str, str, str], ...]  # door_id, colour, destination


@dataclass
class PlanningMemory:
    """Per-episode memory accumulated exclusively from agent observations."""

    visited_rooms: list[str] = field(default_factory=list)
    known_rooms: dict[str, _KnownRoom] = field(default_factory=dict)

    @property
    def visited_set(self) -> set[str]:
        return set(self.visited_rooms)


class PlanningAgent(BaseAgent):
    """Explore new rooms first, using known routes to seek unexplored frontiers.

    Legal moves are always filtered through the currently perceived room rule.
    Among legal doors, unvisited destinations are preferred. If every legal
    destination has been visited, the agent uses BFS over its *discovered* graph
    to move toward a known room with an unvisited, rule-compliant destination.
    Remaining ties are broken by destination and then door ID for repeatability.
    """

    name = "Memory-based planning agent"

    def __init__(self) -> None:
        self.memory = PlanningMemory()

    def reset(self) -> None:
        """Clear knowledge between independent maze episodes."""
        self.memory = PlanningMemory()

    def _remember(self, observation: Observation) -> None:
        if not self.memory.visited_rooms or self.memory.visited_rooms[-1] != observation.room_id:
            self.memory.visited_rooms.append(observation.room_id)
        # Merge rather than replace: the previous-room door is intentionally hidden
        # in later observations, but remains part of what the agent has learned.
        previous = self.memory.known_rooms.get(observation.room_id)
        observed_doors = {
            door_id: (door_id, color, destination)
            for door_id, color, destination in (previous.doors if previous else ())
        }
        observed_doors.update({
            d.door_id: (d.door_id, d.color, d.destination) for d in observation.doors
        })
        self.memory.known_rooms[observation.room_id] = _KnownRoom(
            rule=observation.rule,
            doors=tuple(observed_doors[key] for key in sorted(observed_doors)),
        )

    def _frontier_distance(self, start: str) -> int | None:
        """Shortest known-graph distance to a room with an unexplored legal exit."""
        visited = self.memory.visited_set
        queue = deque([(start, 0)])
        seen = {start}
        while queue:
            room_id, distance = queue.popleft()
            room = self.memory.known_rooms.get(room_id)
            if room is None:
                continue
            unexplored = any(
                destination not in visited and room.rule.allows(color)
                for _, color, destination in room.doors
            )
            if unexplored:
                return distance
            for _, color, destination in sorted(room.doors, key=lambda x: (x[2], x[0])):
                if room.rule.allows(color) and destination in self.memory.known_rooms and destination not in seen:
                    seen.add(destination)
                    queue.append((destination, distance + 1))
        return None

    def choose_door(self, observation: Observation) -> Decision:
        if observation.status.value != "running":
            if observation.status.value == "lost" and observation.room_id not in self.memory.known_rooms:
                # A terminal loss on entry is evidence that the current room was unsafe.
                self.memory.known_rooms[observation.room_id] = _KnownRoom(observation.rule, ())
            return Decision(None, f"Game is already {observation.status.value}; no move selected.", ())

        self._remember(observation)
        legal = rule_compliant_doors(observation.doors, observation.rule)
        if not legal:
            return Decision(None, "No visible door satisfies the room rule.", ())

        visited = self.memory.visited_set
        new_destination_doors = [door for door in legal if door.destination not in visited]
        if new_destination_doors:
            # Prefer a destination that has not been observed at all; then stable IDs.
            selected = min(
                new_destination_doors,
                key=lambda door: (door.destination in self.memory.known_rooms, door.destination, door.door_id),
            )
            considered = tuple(
                door.door_id
                for door in sorted(new_destination_doors, key=lambda d: (d.destination, d.door_id))
            )
            return Decision(
                selected.door_id,
                f"Applied '{observation.rule_text}' and chose an unvisited destination ({selected.destination}) to explore.",
                considered,
            )

        # If all immediate choices are revisits, use discovered routes to seek a frontier.
        scored = []
        for door in legal:
            distance = self._frontier_distance(door.destination)
            scored.append((distance if distance is not None else float("inf"), door.destination, door.door_id, door))
        scored.sort(key=lambda item: (item[0], item[1], item[2]))
        selected = scored[0][3]
        considered = tuple(item[2] for item in scored)
        return Decision(
            selected.door_id,
            f"No unvisited destination is directly available; selected {selected.destination} using the discovered-map frontier estimate.",
            considered,
        )
