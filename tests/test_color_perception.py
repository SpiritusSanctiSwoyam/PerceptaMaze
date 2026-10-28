import unittest
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from agents.rule_first import RuleFirstAgent
from app_scenarios import interactive_scenarios
from maze.environment import GameStatus

class TestColorPerception(unittest.TestCase):
    def test_red_green_collapse_but_other_colors_stay_distinct(self):
        model = ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS)
        self.assertEqual(model.perceive_color("red"), model.perceive_color("green"))
        self.assertEqual(model.perceive_color("blue"), "blue")
        self.assertEqual(model.perceive_color("purple"), "purple")

    def test_instruction_text_remains_readable_while_internal_target_transforms(self):
        sc = interactive_scenarios()[0]; obs = sc.create_maze().observe()
        transformed = ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS).transform(obs)
        self.assertEqual(transformed.rule_text, obs.rule_text)
        self.assertEqual(transformed.rule.color, "red-green ambiguous")

    def test_original_observation_is_not_mutated(self):
        obs = interactive_scenarios()[0].create_maze().observe()
        original = tuple(d.color for d in obs.doors)
        ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS).transform(obs)
        self.assertEqual(tuple(d.color for d in obs.doors), original)

    def test_same_policy_ambiguous_agent_finds_gold(self):
        model = ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS)
        for sc in interactive_scenarios():
            maze = sc.create_maze(); agent = RuleFirstAgent()
            while maze.status is GameStatus.RUNNING:
                maze.step(agent.choose_door(model.transform(maze.observe())).door_id)
            self.assertEqual(maze.status, GameStatus.WON)

if __name__ == "__main__": unittest.main()
