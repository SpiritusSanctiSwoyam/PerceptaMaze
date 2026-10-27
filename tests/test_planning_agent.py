import unittest

from agents.planning_agent import PlanningAgent
from maze.environment import Door, GameStatus, Observation
from maze.rules import RoomRule, RuleKind


def observation(room_id, kind, target, doors, status=GameStatus.RUNNING):
    rule = RoomRule(kind, target)
    return Observation(room_id, rule.describe(), rule, tuple(doors), None, status)


class TestPlanningAgent(unittest.TestCase):
    def setUp(self):
        self.agent = PlanningAgent()

    def test_prefers_unvisited_destination_over_revisit(self):
        first = observation("A", RuleKind.AVOID, "red", [
            Door("to-b", "blue", "B"), Door("to-c", "green", "C")
        ])
        self.agent.choose_door(first)
        # Simulate the agent arriving in B on its next observation.
        second = observation("B", RuleKind.AVOID, "red", [
            Door("to-a", "blue", "A"), Door("to-c", "green", "C")
        ])
        decision = self.agent.choose_door(second)
        self.assertEqual(decision.door_id, "to-c")
        self.assertIn("unvisited", decision.reason)

    def test_obeys_current_room_rule(self):
        obs = observation("A", RuleKind.CHOOSE, "green", [
            Door("blue-door", "blue", "B"), Door("green-door", "green", "C")
        ])
        self.assertEqual(self.agent.choose_door(obs).door_id, "green-door")

    def test_tie_break_is_deterministic(self):
        obs = observation("A", RuleKind.AVOID, "red", [
            Door("z-door", "blue", "Z"), Door("a-door", "green", "B")
        ])
        self.assertEqual(self.agent.choose_door(obs).door_id, "a-door")

    def test_no_legal_move_returns_none(self):
        obs = observation("A", RuleKind.CHOOSE, "green", [Door("blue", "blue", "B")])
        decision = self.agent.choose_door(obs)
        self.assertIsNone(decision.door_id)
        self.assertFalse(decision.has_move)

    def test_terminal_observation_returns_none(self):
        obs = observation("X", RuleKind.AVOID, "red", [], GameStatus.WON)
        self.assertIsNone(self.agent.choose_door(obs).door_id)

    def test_memory_can_be_reset_between_episodes(self):
        obs = observation("A", RuleKind.AVOID, "red", [Door("to-b", "blue", "B")])
        self.agent.choose_door(obs)
        self.assertIn("A", self.agent.memory.visited_set)
        self.agent.reset()
        self.assertEqual(self.agent.memory.visited_rooms, [])
        self.assertEqual(self.agent.memory.known_rooms, {})

    def test_agent_does_not_receive_hidden_environment(self):
        obs = observation("A", RuleKind.AVOID, "red", [Door("to-b", "blue", "B")])
        self.agent.choose_door(obs)
        self.assertFalse(hasattr(self.agent, "environment"))
        self.assertEqual(set(self.agent.memory.known_rooms), {"A"})


if __name__ == "__main__":
    unittest.main()
