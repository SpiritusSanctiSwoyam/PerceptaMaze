import tempfile, unittest
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from evaluation.runner import evaluate_agents, summarise, write_results

class TestEvaluation(unittest.TestCase):
    def test_evaluates_three_agents_on_two_scenarios(self):
        results = evaluate_agents(perception=ColorPerceptionModel(PerceptionMode.RED_GREEN_AMBIGUOUS))
        self.assertEqual(len(results), 6)
        summary = summarise(results)
        self.assertEqual(len(summary), 3)
        self.assertTrue(all("gold_rate_pct" in row for row in summary))

    def test_writes_csv_and_json(self):
        results = evaluate_agents()
        with tempfile.TemporaryDirectory() as tmp:
            csv_path, json_path = write_results(results, tmp)
            self.assertTrue(csv_path.exists()); self.assertTrue(json_path.exists())

if __name__ == "__main__": unittest.main()
