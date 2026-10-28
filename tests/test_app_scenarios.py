import unittest
from app_scenarios import PALETTE, interactive_scenarios

class TestTreeScenarios(unittest.TestCase):
    def test_two_scenarios_each_have_one_gold_exit(self):
        scenarios = interactive_scenarios()
        self.assertEqual(len(scenarios), 2)
        for sc in scenarios:
            golds = [r for r in sc.rooms.values() if r.is_gold_exit]
            self.assertEqual(len(golds), 1)
            self.assertEqual(golds[0].room_id, sc.gold_room)

    def test_every_decision_room_has_three_doors(self):
        for sc in interactive_scenarios():
            for room in sc.rooms.values():
                if not room.is_exit:
                    self.assertEqual(len(room.doors), 3, room.room_id)

    def test_palette_and_rules_vary(self):
        self.assertEqual(set(PALETTE), {"red", "blue", "green", "yellow", "white", "orange", "purple"})
        for sc in interactive_scenarios():
            colors = {d.color for r in sc.rooms.values() for d in r.doors}
            rules = {(r.rule.kind.value, r.rule.color) for r in sc.rooms.values() if r.doors}
            self.assertEqual(colors, set(PALETTE))
            self.assertGreaterEqual(len(rules), 5)

    def test_ambiguous_agent_reaches_gold_on_fixed_route(self):
        from agents.color_perception import ColorPerceptionModel, PerceptionMode
        from agents.rule_first import RuleFirstAgent
        from maze.environment import GameStatus
        model = ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS)
        for sc in interactive_scenarios():
            maze = sc.create_maze(); agent = RuleFirstAgent()
            while maze.status is GameStatus.RUNNING:
                obs = model.transform(maze.observe())
                decision = agent.choose_door(obs)
                maze.step(decision.door_id)
            self.assertEqual(maze.status, GameStatus.WON, sc.name)

if __name__ == "__main__": unittest.main()
