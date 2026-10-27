import unittest

from agents.rule_first import RuleFirstAgent
from maze.environment import Door, GameStatus, Observation
from maze.rules import RoomRule, RuleKind


def observation(kind, target, doors, status=GameStatus.RUNNING):
    rule = RoomRule(kind, target)
    return Observation(
        room_id="R1",
        rule_text=rule.describe(),
        rule=rule,
        doors=tuple(doors),
        previous_room="R0",
        status=status,
    )


class TestRuleFirstAgent(unittest.TestCase):
    def setUp(self):
        self.agent = RuleFirstAgent()

    def test_choose_rule_is_applied_before_tie_break(self):
        obs = observation(
            RuleKind.CHOOSE,
            "green",
            [Door("a-blue", "blue", "R2"), Door("z-green", "green", "R3"), Door("a-green", "green", "R4")],
        )
        decision = self.agent.choose_door(obs)
        self.assertEqual(decision.door_id, "a-green")
        self.assertEqual(decision.considered_doors, ("a-green", "z-green"))

    def test_avoid_rule_then_color_priority(self):
        obs = observation(
            RuleKind.AVOID,
            "red",
            [Door("green-1", "green", "R2"), Door("red-1", "red", "R3"), Door("blue-1", "blue", "R4")],
        )
        self.assertEqual(self.agent.choose_door(obs).door_id, "blue-1")

    def test_same_color_uses_door_id_as_final_tie_break(self):
        obs = observation(
            RuleKind.AVOID,
            "red",
            [Door("z-blue", "blue", "R2"), Door("a-blue", "blue", "R3")],
        )
        self.assertEqual(self.agent.choose_door(obs).door_id, "a-blue")

    def test_no_valid_doors_returns_no_move(self):
        obs = observation(RuleKind.CHOOSE, "green", [Door("red-1", "red", "R2")])
        decision = self.agent.choose_door(obs)
        self.assertIsNone(decision.door_id)
        self.assertFalse(decision.has_move)

    def test_terminal_observation_returns_no_move(self):
        obs = observation(RuleKind.AVOID, "red", [Door("blue-1", "blue", "R2")], GameStatus.WON)
        self.assertIsNone(self.agent.choose_door(obs).door_id)

    def test_agent_receives_observation_not_environment(self):
        obs = observation(RuleKind.AVOID, "red", [Door("blue-1", "blue", "R2")])
        self.assertFalse(hasattr(obs, "rooms"))
        self.assertFalse(hasattr(obs, "_rooms"))
        self.assertEqual(self.agent.choose_door(obs).door_id, "blue-1")


if __name__ == "__main__":
    unittest.main()
