import tempfile
import unittest
from pathlib import Path

from agents.color_perception import ColorPerceptionModel, PerceptionMode
from agents.planning_agent import PlanningAgent
from agents.rule_first import RuleFirstAgent
from evaluation.runner import evaluate_agents, run_episode, scenario_suite, summarise, write_results


class TestEvaluationRunner(unittest.TestCase):
    def test_suite_has_named_reproducible_scenarios(self):
        first = scenario_suite()
        second = scenario_suite()
        self.assertEqual([s.name for s in first], [s.name for s in second])
        self.assertGreaterEqual(len(first), 5)

    def test_both_agents_are_evaluated_on_same_scenarios(self):
        results = evaluate_agents()
        expected = len(scenario_suite())
        self.assertEqual(len(results), expected * 2)
        self.assertEqual({r.agent for r in results}, {RuleFirstAgent.name, PlanningAgent.name})
        self.assertEqual({r.scenario for r in results}, {s.name for s in scenario_suite()})

    def test_rule_first_baseline_has_known_dead_end_case(self):
        scenario = next(s for s in scenario_suite() if s.name == "choice_trap")
        result = run_episode(RuleFirstAgent(), scenario)
        self.assertFalse(result.won)
        self.assertEqual(result.dead_end_losses, 1)

    def test_colour_ambiguity_mode_is_recorded(self):
        scenario = next(s for s in scenario_suite() if s.name == "safe_route")
        result = run_episode(
            RuleFirstAgent(), scenario,
            ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS),
        )
        self.assertEqual(result.perception_mode, "red_green_ambiguous")

    def test_summary_has_rates_and_counts(self):
        results = evaluate_agents()
        summary = summarise(results)
        self.assertEqual(len(summary), 2)
        for row in summary:
            self.assertIn("win_rate_pct", row)
            self.assertIn("rule_compliance_pct", row)
            self.assertGreaterEqual(row["win_rate_pct"], 0)
            self.assertLessEqual(row["win_rate_pct"], 100)

    def test_results_write_csv_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = evaluate_agents()
            csv_path, json_path = write_results(results, tmp)
            self.assertTrue(csv_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("scenario", csv_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertIn("win_rate_pct", json_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
