"""Deterministic perception-aware baseline with fixed door-order fallback."""
from agents.base_agent import BaseAgent, Decision
from maze.environment import Observation
from maze.rules import RuleKind


class RuleFirstAgent(BaseAgent):
    name = "Rule-first baseline"

    def choose_door(self, observation: Observation) -> Decision:
        if observation.status.value != "running":
            return Decision(None, "Episode is terminal.", ())
        doors = list(observation.doors)
        if not doors:
            return Decision(None, "No doors are available.", ())
        target = observation.rule.color.casefold()
        if observation.rule.kind is RuleKind.CHOOSE:
            matches = [d for d in doors if d.color.casefold() == target]
            if matches:
                selected = matches[0]
                return Decision(selected.door_id, f"Matched perceived target {target}.", tuple(d.door_id for d in matches))
            selected = doors[0]
            return Decision(selected.door_id, f"Target {target} is absent; used fixed door-order fallback.", tuple(d.door_id for d in doors))
        legal = [d for d in doors if d.color.casefold() != target]
        if legal:
            selected = legal[0]
            return Decision(selected.door_id, f"Applied AVOID {target}; selected first compliant door.", tuple(d.door_id for d in legal))
        selected = doors[0]
        return Decision(selected.door_id, "No door avoids the target; used fixed door-order fallback.", tuple(d.door_id for d in doors))
