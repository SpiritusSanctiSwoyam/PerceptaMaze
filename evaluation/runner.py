"""Reproducible evaluation for both perception modes and all three agents."""
from __future__ import annotations
import argparse, csv, json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable
from agents.base_agent import BaseAgent
from agents.rule_first import RuleFirstAgent
from agents.planning_agent import PlanningAgent
from agents.gold_hunter import GoldHunterAgent
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from app_scenarios import Scenario, interactive_scenarios
from maze.environment import GameStatus

@dataclass
class EpisodeResult:
    agent: str
    scenario: str
    perception_mode: str
    status: str
    moves: int
    rule_compliant_moves: int
    invalid_attempts: int
    dead_end_losses: int
    no_legal_move_losses: int
    won: bool
    attempts: int = 1
    gold_found: bool = False
    error: str = ""


def _play_one(agent: BaseAgent, scenario: Scenario, perception: ColorPerceptionModel | None, max_steps: int = 8):
    maze = scenario.create_maze()
    moves = compliant = invalid = 0
    error = ""
    for _ in range(max_steps):
        if maze.status is not GameStatus.RUNNING:
            break
        true_obs = maze.observe()
        obs = perception.transform(true_obs) if perception else true_obs
        decision = agent.choose_door(obs)
        if not decision.has_move:
            error = decision.reason
            invalid += 1
            break
        selected = next((d for d in true_obs.doors if d.door_id == decision.door_id), None)
        if selected is None:
            error = f"Unavailable door {decision.door_id}"
            invalid += 1
            break
        if true_obs.rule.allows(selected.color) or (scenario.rooms[true_obs.room_id].red_green_equivalence and selected.color in {"red", "green"}):
            compliant += 1
        try:
            maze.step(selected.door_id)
            moves += 1
        except ValueError as exc:
            error = str(exc)
            invalid += 1
            break
    if maze.status is GameStatus.RUNNING:
        error = error or "Episode exceeded the move limit."
    return maze, moves, compliant, invalid, error


def run_episode(agent: BaseAgent, scenario: Scenario, perception: ColorPerceptionModel | None = None, max_steps: int = 8) -> EpisodeResult:
    if hasattr(agent, "reset"):
        agent.reset()
    maze, moves, compliant, invalid, error = _play_one(agent, scenario, perception, max_steps)
    return EpisodeResult(agent.name, scenario.name, perception.mode.value if perception else "normal", maze.status.value, moves, compliant, invalid, 0, 0, maze.status is GameStatus.WON, 1, maze.status is GameStatus.WON, error)


def run_gold_hunter(agent: GoldHunterAgent, scenario: Scenario, perception: ColorPerceptionModel | None = None) -> EpisodeResult:
    agent.reset()
    total_moves = total_compliant = total_invalid = 0
    final_status = GameStatus.EXITED
    error = ""
    attempts_used = 0
    for attempt in range(agent.MAX_ATTEMPTS):
        agent.begin_attempt()
        maze, moves, compliant, invalid, err = _play_one(agent, scenario, perception, max_steps=3)
        attempts_used += 1
        total_moves += moves
        total_compliant += compliant
        total_invalid += invalid
        final_status = maze.status
        error = error or err
        agent.finish_attempt(maze.status is GameStatus.WON)
        if maze.status is GameStatus.WON:
            break
    return EpisodeResult(agent.name, scenario.name, perception.mode.value if perception else "normal", final_status.value, total_moves, total_compliant, total_invalid, 0, 0, final_status is GameStatus.WON, attempts_used, final_status is GameStatus.WON, error)


def evaluate_agents(agent_factories: dict[str, Callable[[], BaseAgent]] | None = None, scenarios: Iterable[Scenario] | None = None, perception: ColorPerceptionModel | None = None) -> list[EpisodeResult]:
    factories = agent_factories or {RuleFirstAgent.name: RuleFirstAgent, PlanningAgent.name: PlanningAgent, GoldHunterAgent.name: GoldHunterAgent}
    selected_scenarios = tuple(scenarios or interactive_scenarios())
    results = []
    for label, factory in factories.items():
        for scenario in selected_scenarios:
            agent = factory()
            result = run_gold_hunter(agent, scenario, perception) if isinstance(agent, GoldHunterAgent) else run_episode(agent, scenario, perception)
            result.agent = label
            results.append(result)
    return results


def summarise(results: Iterable[EpisodeResult]) -> list[dict[str, object]]:
    groups: dict[tuple[str, str], list[EpisodeResult]] = {}
    for r in results:
        groups.setdefault((r.agent, r.perception_mode), []).append(r)
    output = []
    for (agent, mode), rows in sorted(groups.items()):
        n = len(rows)
        output.append({"agent": agent, "perception_mode": mode, "scenarios": n, "gold_found": sum(r.gold_found for r in rows), "gold_rate_pct": round(100 * sum(r.gold_found for r in rows) / n, 2) if n else 0.0, "mean_moves": round(sum(r.moves for r in rows) / n, 2) if n else 0.0, "mean_attempts": round(sum(r.attempts for r in rows) / n, 2) if n else 0.0, "invalid_attempts": sum(r.invalid_attempts for r in rows)})
    return output


def write_results(results: list[EpisodeResult], output_dir: str | Path = "results") -> tuple[Path, Path]:
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    csv_path, json_path = out / "episode_results.csv", out / "summary.json"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(EpisodeResult.__dataclass_fields__))
        writer.writeheader(); writer.writerows(asdict(r) for r in results)
    json_path.write_text(json.dumps(summarise(results), indent=2) + "\n", encoding="utf-8")
    return csv_path, json_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results")
    parser.add_argument("--perception", choices=[m.value for m in PerceptionMode], default="normal")
    args = parser.parse_args()
    mode = PerceptionMode(args.perception)
    perception = None if mode is PerceptionMode.NORMAL else ColorPerceptionModel(mode)
    results = evaluate_agents(perception=perception)
    csv_path, json_path = write_results(results, args.output_dir)
    print(json.dumps(summarise(results), indent=2))
    print(f"Wrote {csv_path} and {json_path}")

if __name__ == "__main__":
    main()
