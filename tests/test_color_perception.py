import unittest

from agents.color_perception import ColorPerceptionModel, PerceptionMode
from agents.rule_first import RuleFirstAgent
from maze.environment import Door, GameStatus, Observation
from maze.rules import RoomRule, RuleKind


class TestColorPerceptionModel(unittest.TestCase):
    def setUp(self):
        rule = RoomRule(RuleKind.CHOOSE, "green")
        self.observation = Observation(
            room_id="R1",
            rule_text=rule.describe(),
            rule=rule,
            doors=(
                Door("red-door", "red", "R2"),
                Door("green-door", "green", "R3"),
                Door("blue-door", "blue", "R4"),
            ),
            previous_room="R0",
            status=GameStatus.RUNNING,
        )

    def test_red_and_green_become_ambiguous(self):
        model = ColorPerceptionModel()
        self.assertEqual(model.perceive_color("red"), "red-green ambiguous")
        self.assertEqual(model.perceive_color("GREEN"), "red-green ambiguous")
        self.assertEqual(model.perceive_color("blue"), "blue")

    def test_normal_mode_preserves_original_observation(self):
        model = ColorPerceptionModel(PerceptionMode.NORMAL)
        self.assertIs(model.transform(self.observation), self.observation)

    def test_transformation_preserves_door_ids_and_destinations(self):
        perceived = ColorPerceptionModel().transform(self.observation)
        self.assertEqual(
            [(d.door_id, d.destination) for d in perceived.doors],
            [(d.door_id, d.destination) for d in self.observation.doors],
        )

    def test_transformation_does_not_mutate_original(self):
        ColorPerceptionModel().transform(self.observation)
        self.assertEqual(self.observation.rule.color, "green")
        self.assertEqual([d.color for d in self.observation.doors], ["red", "green", "blue"])

    def test_rule_first_agent_can_choose_based_on_ambiguous_observation(self):
        perceived = ColorPerceptionModel().transform(self.observation)
        decision = RuleFirstAgent().choose_door(perceived)
        # The perceived model cannot distinguish red from green, so the fixed
        # door-ID tie-break chooses green-door in this constructed example.
        self.assertEqual(decision.door_id, "green-door")

    def test_blue_remains_distinct_under_avoid_rule(self):
        rule = RoomRule(RuleKind.AVOID, "red")
        obs = Observation(
            room_id="R1", rule_text=rule.describe(), rule=rule,
            doors=(Door("a-red", "red", "R2"), Door("z-blue", "blue", "R3")),
            previous_room=None, status=GameStatus.RUNNING,
        )
        perceived = ColorPerceptionModel().transform(obs)
        decision = RuleFirstAgent().choose_door(perceived)
        self.assertEqual(decision.door_id, "z-blue")


if __name__ == "__main__":
    unittest.main()
