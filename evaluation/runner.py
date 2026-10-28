"""Run reproducible agent evaluations against a shared maze scenario suite.

The runner deliberately keeps the environment's hidden graph away from agents:
only ``maze.observe()`` (optionally transformed by a perception model) is passed
into ``choose_door``. An invalid choice ends that evaluation episode as a failed
attempt, even though the interactive game engine itself rejects the move; this
keeps batch evaluation bounded and makes perception-related failures measurable.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

from agents.base_agent import BaseAgent
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from agents.planning_agent import PlanningAgent
from agents.rule_first import RuleFirstAgent
from maze.environment import Door, GameStatus, PerceptaMaze, Room
from maze.rules import RoomRule, RuleKind, rule_compliant_doors


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    rooms: dict[str, Room]
    start_room: str
    exit_room: str

    def create_maze(self) -> PerceptaMaze:
        """Return a fresh environment for this episode."""
        return PerceptaMaze(self.rooms, self.start_room, self.exit_room)


def scenario_suite() -> tuple[Scenario, ...]:
    """Small, fixed benchmark suite; both agents receive identical scenarios."""
    return (
        Scenario(
            "direct_exit",
            "A legal move leads directly from the start to the exit.",
            {
                "S": Room("S", RoomRule(RuleKind.CHOOSE, "blue"), (Door("s-exit", "blue", "X"), Door("s-dead", "red", "D"))),
                "D": Room("D", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
            }, "S", "X",
        ),
        Scenario(
            "safe_route",
            "A short compliant route reaches the exit; a different legal colour leads to a dead end.",
            {
                "S": Room("S", RoomRule(RuleKind.AVOID, "red"), (Door("s-blue", "blue", "A"), Door("s-green", "green", "D"), Door("s-red", "red", "B"))),
                "A": Room("A", RoomRule(RuleKind.CHOOSE, "green"), (Door("a-back", "blue", "S"), Door("a-green", "green", "X"))),
                "B": Room("B", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "D": Room("D", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
            }, "S", "X",
        ),
        Scenario(
            "choice_trap",
            "The deterministic colour tie-break can select a dead-end route.",
            {
                "S": Room("S", RoomRule(RuleKind.AVOID, "red"), (Door("s-blue-dead", "blue", "D"), Door("s-green-safe", "green", "A"), Door("s-red", "red", "B"))),
                "A": Room("A", RoomRule(RuleKind.CHOOSE, "blue"), (Door("a-back", "green", "S"), Door("a-blue-exit", "blue", "X"))),
                "B": Room("B", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "D": Room("D", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
            }, "S", "X",
        ),
        Scenario(
            "no_legal_door",
            "The start instruction has no compliant door after applying the game rules.",
            {
                "S": Room("S", RoomRule(RuleKind.CHOOSE, "green"), (Door("s-blue", "blue", "A"),)),
                "A": Room("A", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
            }, "S", "X",
        ),
        Scenario(
            "multi_step",
            "A three-room route tests decisions across successive observations.",
            {
                "S": Room("S", RoomRule(RuleKind.CHOOSE, "green"), (Door("s-green", "green", "A"), Door("s-red-dead", "red", "D"))),
                "A": Room("A", RoomRule(RuleKind.AVOID, "red"), (Door("a-back", "blue", "S"), Door("a-green", "green", "B"))),
                "B": Room("B", RoomRule(RuleKind.CHOOSE, "blue"), (Door("b-back", "green", "A"), Door("b-blue", "blue", "X"))),
                "D": Room("D", RoomRule(RuleKind.AVOID, "red"), (), is_dead_end=True),
                "X": Room("X", RoomRule(RuleKind.AVOID, "red"), (), is_exit=True),
            }, "S", "X",
        ),
    )


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
    error: str = ""


def run_episode(
    agent: BaseAgent,
    scenario: Scenario,
    perception: ColorPerceptionModel | None = None,
    max_steps: int = 32,
) -> EpisodeResult:
    """Run one episode and return outcome and behaviour metrics."""
    maze = scenario.create_maze()
    reset = getattr(agent, "reset", None)
    if callable(reset):
        reset()
    mode_name = perception.mode.value if perception else PerceptionMode.NORMAL.value
    moves = compliant_moves = invalid_attempts = dead_end_losses = no_legal_move_losses = 0
    error = ""

    while maze.status is GameStatus.RUNNING and moves < max_steps:
        true_observation = maze.observe()
        agent_observation = perception.transform(true_observation) if perception else true_observation
        decision = agent.choose_door(agent_observation)
        if not decision.has_move:
            # The engine declares loss when there are no truly compliant doors.
            legal = rule_compliant_doors(true_observation.doors, true_observation.rule)
            if not legal:
                result = maze.step("__no_legal_move__")
                no_legal_move_losses += int(result.status is GameStatus.LOST)
            else:
                # A no-move decision despite legal doors is treated as a failed agent action.
                error = "Agent returned no move although a legal door was available."
                invalid_attempts += 1
                maze.status = GameStatus.LOST
            break

        selected = next((d for d in true_observation.doors if d.door_id == decision.door_id), None)
        if selected is None:
            error = f"Agent selected unavailable door: {decision.door_id}"
            invalid_attempts += 1
            maze.status = GameStatus.LOST
            break
        is_compliant = true_observation.rule.allows(selected.color)
        if is_compliant:
            compliant_moves += 1
        try:
            step_result = maze.step(decision.door_id)
            moves += 1
        except ValueError as exc:
            error = str(exc)
            invalid_attempts += 1
            maze.status = GameStatus.LOST
            break

        if step_result.status is GameStatus.LOST and step_result.entered_room is not None:
            entered = step_result.entered_room
            # Inspect outcome only for scoring; never expose this information to the agent.
            if scenario.rooms[entered].is_dead_end:
                dead_end_losses += 1
        if step_result.status is GameStatus.LOST and "No available door" in step_result.message:
            no_legal_move_losses += 1

    if maze.status is GameStatus.RUNNING:
        maze.status = GameStatus.LOST
        error = error or f"Episode exceeded max_steps={max_steps}."

    return EpisodeResult(
        agent=agent.name,
        scenario=scenario.name,
        perception_mode=mode_name,
        status=maze.status.value,
        moves=moves,
        rule_compliant_moves=compliant_moves,
        invalid_attempts=invalid_attempts,
        dead_end_losses=dead_end_losses,
        no_legal_move_losses=no_legal_move_losses,
        won=maze.status is GameStatus.WON,
        error=error,
    )


def evaluate_agents(
    agent_factories: dict[str, Callable[[], BaseAgent]] | None = None,
    scenarios: Iterable[Scenario] | None = None,
    perception: ColorPerceptionModel | None = None,
) -> list[EpisodeResult]:
    """Evaluate each agent on each scenario, creating a fresh agent per episode."""
    factories = agent_factories or {
        RuleFirstAgent.name: RuleFirstAgent,
        PlanningAgent.name: PlanningAgent,
    }
    selected_scenarios = tuple(scenarios or scenario_suite())
    results: list[EpisodeResult] = []
    for agent_name, factory in factories.items():
        for scenario in selected_scenarios:
            result = run_episode(factory(), scenario, perception=perception)
            # Keep the registered label stable for custom factories.
            result.agent = agent_name
            results.append(result)
    return results


def summarise(results: Iterable[EpisodeResult]) -> list[dict[str, object]]:
    """Aggregate episode results by agent and perception mode."""
    groups: dict[tuple[str, str], list[EpisodeResult]] = {}
    for result in results:
        groups.setdefault((result.agent, result.perception_mode), []).append(result)
    summary: list[dict[str, object]] = []
    for (agent, mode), episodes in sorted(groups.items()):
        count = len(episodes)
        total_moves = sum(item.moves for item in episodes)
        compliant = sum(item.rule_compliant_moves for item in episodes)
        attempted_actions = total_moves + sum(item.invalid_attempts for item in episodes)
        summary.append({
            "agent": agent,
            "perception_mode": mode,
            "episodes": count,
            "wins": sum(item.won for item in episodes),
            "win_rate_pct": round(100 * sum(item.won for item in episodes) / count, 2) if count else 0.0,
            "mean_moves": round(total_moves / count, 2) if count else 0.0,
            "rule_compliance_pct": round(100 * compliant / attempted_actions, 2) if attempted_actions else 0.0,
            "dead_end_losses": sum(item.dead_end_losses for item in episodes),
            "no_legal_move_losses": sum(item.no_legal_move_losses for item in episodes),
            "invalid_attempts": sum(item.invalid_attempts for item in episodes),
        })
    return summary


def write_results(results: list[EpisodeResult], output_dir: str | Path = "results") -> tuple[Path, Path]:
    """Write per-episode CSV and aggregate JSON files."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    episode_path = destination / "episode_results.csv"
    summary_path = destination / "summary.json"
    rows = [asdict(result) for result in results]
    with episode_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(EpisodeResult.__dataclass_fields__))
        writer.writeheader()
        writer.writerows(rows)
    with summary_path.open("w", encoding="utf-8") as handle:
        json.dump(summarise(results), handle, indent=2)
        handle.write("\n")
    return episode_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate PerceptaMaze agents on fixed scenarios.")
    parser.add_argument("--output-dir", default="results", help="Directory for CSV and JSON results")
    parser.add_argument("--perception", choices=[mode.value for mode in PerceptionMode], default=PerceptionMode.NORMAL.value)
    args = parser.parse_args()
    perception = None if args.perception == PerceptionMode.NORMAL.value else ColorPerceptionModel(PerceptionMode(args.perception))
    results = evaluate_agents(perception=perception)
    episode_path, summary_path = write_results(results, args.output_dir)
    print("Aggregate results:")
    print(json.dumps(summarise(results), indent=2))
    print(f"\nEpisode details: {episode_path}")
    print(f"Aggregate summary: {summary_path}")


if __name__ == "__main__":
    main()
