"""Memory-based exploration agent; uses only observations it has received."""
from dataclasses import dataclass, field
from agents.base_agent import BaseAgent, Decision
from maze.environment import Observation
from maze.rules import RuleKind


@dataclass
class PlanningMemory:
    visited_rooms: list[str] = field(default_factory=list)
    known_doors: dict[str, tuple[tuple[str, str, str], ...]] = field(default_factory=dict)


class PlanningAgent(BaseAgent):
    name = "Memory-based planning agent"
    def __init__(self):
        self.memory = PlanningMemory()
    def reset(self):
        self.memory = PlanningMemory()
    def choose_door(self, observation: Observation) -> Decision:
        if observation.status.value != "running":
            return Decision(None, "Episode is terminal.", ())
        if not self.memory.visited_rooms or self.memory.visited_rooms[-1] != observation.room_id:
            self.memory.visited_rooms.append(observation.room_id)
        self.memory.known_doors[observation.room_id] = tuple((d.door_id, d.color, d.destination) for d in observation.doors)
        doors = list(observation.doors)
        if not doors:
            return Decision(None, "No doors are available.", ())
        target = observation.rule.color.casefold()
        if observation.rule.kind is RuleKind.CHOOSE:
            matches = [d for d in doors if d.color.casefold() == target]
            candidates = matches or doors
            reason = f"Matched perceived target {target}." if matches else f"Target {target} absent; fallback candidates ordered by discovered history."
        else:
            candidates = [d for d in doors if d.color.casefold() != target] or doors
            reason = f"Applied AVOID {target} and chose a legal door."
        visited_destinations = set(self.memory.visited_rooms)
        unvisited = [d for d in candidates if d.destination not in visited_destinations]
        selected = (unvisited or candidates)[0]
        return Decision(selected.door_id, reason + f" Selected destination {selected.destination}.", tuple(d.door_id for d in candidates))
