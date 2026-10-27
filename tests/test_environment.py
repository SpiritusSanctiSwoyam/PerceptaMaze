import unittest

from maze.environment import Door, GameStatus, InvalidMove, PerceptaMaze, Room
from maze.rules import RoomRule, RuleKind


def make_maze():
    rooms = {
        "S": Room(
            "S",
            RoomRule(RuleKind.AVOID, "red"),
            (Door("s-blue", "blue", "A"), Door("s-red", "red", "D")),
        ),
        "A": Room(
            "A",
            RoomRule(RuleKind.CHOOSE, "green"),
            (Door("a-back", "blue", "S"), Door("a-green", "green", "B")),
        ),
        "B": Room("B", RoomRule(RuleKind.AVOID, "red"), (Door("b-exit", "blue", "X"),)),
        "D": Room("D", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
        "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
    }
    return PerceptaMaze(rooms, start_room="S", exit_room="X")


class TestRulesAndEnvironment(unittest.TestCase):
    def test_avoid_rule_rejects_target_colour(self):
        maze = make_maze()
        with self.assertRaises(InvalidMove):
            maze.step("s-red")
        self.assertEqual(maze.current_room, "S")

    def test_choose_rule_requires_target_colour(self):
        maze = make_maze()
        maze.step("s-blue")
        with self.assertRaises(InvalidMove):
            maze.step("a-back")
        self.assertEqual(maze.current_room, "A")

    def test_previous_room_door_is_hidden_and_cannot_be_used(self):
        maze = make_maze()
        maze.step("s-blue")
        observation = maze.observe()
        self.assertEqual([door.door_id for door in observation.doors], ["a-green"])
        maze.step("a-green")
        with self.assertRaises(InvalidMove):
            maze.step("b-back")

    def test_dead_end_causes_immediate_loss(self):
        maze = make_maze()
        # Construct a valid rule-compliant path into the dead end.
        rooms = {
            "S": Room("S", RoomRule(RuleKind.CHOOSE, "red"), (Door("to-dead", "red", "D"),)),
            "D": Room("D", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
            "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
        }
        maze = PerceptaMaze(rooms, "S", "X")
        result = maze.step("to-dead")
        self.assertEqual(result.status, GameStatus.LOST)
        self.assertIn("dead-end", result.message)
        with self.assertRaises(RuntimeError):
            maze.step("anything")

    def test_rule_with_no_legal_doors_causes_loss(self):
        rooms = {
            "S": Room("S", RoomRule(RuleKind.CHOOSE, "red"), (Door("to-a", "red", "A"),)),
            "A": Room("A", RoomRule(RuleKind.CHOOSE, "red"), (Door("back", "blue", "S"),)),
            "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
        }
        maze = PerceptaMaze(rooms, "S", "X")
        maze.step("to-a")
        # Even an attempted action triggers the no-legal-move terminal rule.
        result = maze.step("back")
        self.assertEqual(result.status, GameStatus.LOST)
        self.assertIn("No available door", result.message)

    def test_observation_does_not_expose_full_map(self):
        maze = make_maze()
        observation = maze.observe()
        self.assertFalse(hasattr(observation, "rooms"))
        self.assertEqual(observation.room_id, "S")
        self.assertEqual(observation.status, GameStatus.RUNNING)

    def test_reaching_exit_wins(self):
        rooms = {
            "S": Room("S", RoomRule(RuleKind.CHOOSE, "blue"), (Door("to-exit", "blue", "X"),)),
            "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
        }
        maze = PerceptaMaze(rooms, "S", "X")
        result = maze.step("to-exit")
        self.assertEqual(result.status, GameStatus.WON)


if __name__ == "__main__":
    unittest.main()
