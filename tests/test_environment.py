import unittest
from app_scenarios import interactive_scenarios
from maze.environment import GameStatus, InvalidMove

class TestTreeEnvironment(unittest.TestCase):
    def test_only_gold_exit_wins(self):
        sc = interactive_scenarios()[0]
        maze = sc.create_maze()
        # The environment has exactly one Gold leaf.
        golds = [rid for rid, room in sc.rooms.items() if room.is_gold_exit]
        self.assertEqual(golds, [sc.gold_room])
        self.assertTrue(sc.rooms[sc.gold_room].is_exit)

    def test_observation_only_exposes_current_room(self):
        maze = interactive_scenarios()[0].create_maze()
        obs = maze.observe()
        self.assertEqual(len(obs.doors), 3)
        self.assertFalse(hasattr(obs, "rooms"))

    def test_ordinary_exit_is_not_a_win(self):
        sc = interactive_scenarios()[0]
        maze = sc.create_maze()
        maze.step("S-0")  # scenario 1: fixed first door is the ordinary branch
        from agents.rule_first import RuleFirstAgent
        agent = RuleFirstAgent()
        # Follow the deterministic normal-vision policy until an ordinary exit.
        while maze.status is GameStatus.RUNNING:
            decision = agent.choose_door(maze.observe())
            maze.step(decision.door_id)
        self.assertEqual(maze.status, GameStatus.EXITED)
        self.assertNotEqual(maze.status, GameStatus.WON)

    def test_invalid_door_is_rejected(self):
        maze = interactive_scenarios()[0].create_maze()
        with self.assertRaises(InvalidMove):
            maze.step("not-a-door")

if __name__ == "__main__": unittest.main()
