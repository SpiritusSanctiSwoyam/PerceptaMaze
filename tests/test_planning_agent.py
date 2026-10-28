import unittest
from agents.planning_agent import PlanningAgent
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from app_scenarios import interactive_scenarios
from maze.environment import GameStatus

class TestPlanningAgent(unittest.TestCase):
    def test_agent_finds_gold_with_ambiguous_perception(self):
        model = ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS)
        for sc in interactive_scenarios():
            maze = sc.create_maze(); agent = PlanningAgent()
            while maze.status is GameStatus.RUNNING:
                decision = agent.choose_door(model.transform(maze.observe()))
                self.assertTrue(decision.has_move)
                maze.step(decision.door_id)
            self.assertEqual(maze.status, GameStatus.WON)

    def test_memory_records_observed_rooms_only(self):
        sc = interactive_scenarios()[0]; maze = sc.create_maze(); agent = PlanningAgent()
        agent.choose_door(maze.observe())
        self.assertEqual(agent.memory.visited_rooms, ["S"])
        self.assertEqual(set(agent.memory.known_doors), {"S"})

    def test_reset_clears_memory(self):
        maze = interactive_scenarios()[0].create_maze(); agent = PlanningAgent()
        agent.choose_door(maze.observe()); agent.reset()
        self.assertEqual(agent.memory.visited_rooms, [])

if __name__ == "__main__": unittest.main()
