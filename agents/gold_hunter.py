"""Bounded repeated-attempt agent that systematically tests route signatures."""
from dataclasses import dataclass, field
from agents.base_agent import BaseAgent, Decision
from maze.environment import Observation
from maze.rules import RuleKind


@dataclass
class HunterMemory:
    attempts_started: int = 0
    current_attempt: int = 0
    depth: int = 0
    attempted_signatures: set[tuple[int, int, int]] = field(default_factory=set)
    route_history: list[tuple[str, ...]] = field(default_factory=list)
    current_route: list[str] = field(default_factory=list)


class GoldHunterAgent(BaseAgent):
    """Tries up to ten complete routes, learning which route signatures failed.

    The route order explores the middle root branch first, then enumerates its
    child and leaf choices. This is still observation-driven: at each room the
    agent chooses a door by its position in the currently visible door list.
    It never reads the hidden maze graph or Gold location.
    """
    name = "Gold Hunter (10 attempts)"
    MAX_ATTEMPTS = 10
    def __init__(self):
        self.memory = HunterMemory()
    def reset(self):
        # Evaluation creates a fresh instance per episode; UI can call begin_attempt
        # to retain knowledge between repeated runs.
        self.memory = HunterMemory()
    def begin_attempt(self):
        self.memory.current_attempt = self.memory.attempts_started
        self.memory.attempts_started += 1
        self.memory.depth = 0
        self.memory.current_route = []
    @staticmethod
    def _signature_for(attempt: int) -> tuple[int, int, int]:
        # First nine attempts exhaust all second/third-level combinations beneath
        # root door index 1; the remaining attempt explores root door index 0.
        if attempt < 9:
            return (1, attempt // 3, attempt % 3)
        return (0, 0, 0)
    def choose_door(self, observation: Observation) -> Decision:
        if observation.status.value != "running":
            return Decision(None, "Episode is terminal.", ())
        if self.memory.attempts_started == 0:
            self.begin_attempt()
        if self.memory.attempts_started > self.MAX_ATTEMPTS:
            return Decision(None, "Gold Hunter reached its ten-attempt limit.", ())
        doors = list(observation.doors)
        if not doors:
            return Decision(None, "No doors are available.", ())
        signature = self._signature_for(self.memory.current_attempt)
        depth = min(self.memory.depth, 2)
        index = min(signature[depth], len(doors) - 1)
        selected = doors[index]
        self.memory.current_route.append(selected.door_id)
        self.memory.depth += 1
        return Decision(selected.door_id, f"Attempt {self.memory.current_attempt + 1}/{self.MAX_ATTEMPTS}: testing route choice {index + 1} at depth {depth + 1}.", tuple(d.door_id for d in doors))
    def finish_attempt(self, gold_found: bool):
        self.memory.route_history.append(tuple(self.memory.current_route))
        self.memory.current_route = []
        if not gold_found:
            self.memory.depth = 0
