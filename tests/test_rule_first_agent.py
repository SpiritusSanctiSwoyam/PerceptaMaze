import unittest
from agents.rule_first import RuleFirstAgent
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from app_scenarios import interactive_scenarios
from maze.environment import GameStatus

class TestRuleFirstAgent(unittest.TestCase):
    def test_fixed_fallback_misses_gold_with_normal_vision(self):
        sc = interactive_scenarios()[0]; maze = sc.create_maze(); agent = RuleFirstAgent()
        while maze.status is GameStatus.RUNNING:
            decision = agent.choose_door(maze.observe())
            maze.step(decision.door_id)
        self.assertEqual(maze.status, GameStatus.EXITED)

    def test_ambiguous_perception_finds_gold(self):
        sc = interactive_scenarios()[0]; maze = sc.create_maze(); agent = RuleFirstAgent()
        model = ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS)
        while maze.status is GameStatus.RUNNING:
            decision = agent.choose_door(model.transform(maze.observe()))
            maze.step(decision.door_id)
        self.assertEqual(maze.status, GameStatus.WON)

if __name__ == "__main__": unittest.main()
