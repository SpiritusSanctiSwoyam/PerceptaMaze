import unittest

from app_scenarios import four_by_four_scenario, interactive_scenarios
from maze.environment import GameStatus
from maze.rules import rule_compliant_doors


class TestInteractiveScenarios(unittest.TestCase):
    def test_four_by_four_scenario_has_sixteen_rooms_and_valid_exit(self):
        scenario = four_by_four_scenario()
        self.assertEqual(len(scenario.rooms), 16)
        self.assertTrue(scenario.rooms[scenario.exit_room].is_exit)
        self.assertEqual(scenario.start_room, "R00")

    def test_safe_route_reaches_exit(self):
        maze = four_by_four_scenario().create_maze()
        expected = ["R01", "R02", "R03", "R13", "R23", "R33"]
        for destination in expected:
            observation = maze.observe()
            legal = rule_compliant_doors(observation.doors, observation.rule)
            selected = next((door for door in legal if door.destination == destination), None)
            self.assertIsNotNone(selected, f"No compliant door to {destination}")
            result = maze.step(selected.door_id)
        self.assertIs(result.status, GameStatus.WON)

    def test_interactive_scenarios_include_benchmark_and_grid_maze(self):
        names = {scenario.name for scenario in interactive_scenarios()}
        self.assertIn("four_by_four", names)
        self.assertIn("direct_exit", names)


if __name__ == "__main__":
    unittest.main()
