# PerceptaMaze

PerceptaMaze is an AI maze game prototype in which an agent sees only its current room, reads a colour-based instruction, and chooses one of the available doors. The project will compare simple rule-following agents with an AI planning agent.

## Current status

The environment, deterministic rule-first baseline agent, configurable simulated colour-perception model, and memory-based planning agent are implemented. The engine enforces room instructions, partial observations, no-backtracking, dead-end losses, and exit wins. Unit tests cover the environment and agent behaviour. The Streamlit interface and evaluation metrics are implemented; deployment to Streamlit Community Cloud is the next milestone.

## Game rules

1. The maze is a graph represented visually as a 4×4 grid in the planned interface. Each room has a rule and zero or more coloured doors.
2. A room rule is either **Choose COLOUR** or **Do not choose COLOUR**.
3. An agent sees only the current room's instruction and its available doors. The complete maze is hidden from the agent.
4. The door leading directly back to the previous room is unavailable. Backtracking is forbidden.
5. The chosen door must comply with the room's rule. An invalid choice is rejected and does not move the agent.
6. Entering a designated dead-end room causes an immediate loss.
7. Entering the exit room wins the game.
8. If no available door satisfies the room's instruction, the environment records a loss.
9. The initial environment is deterministic. Colour-vision-deficiency perception will be a separately documented simulation model, not a claim about every person's perception.

## Rule-first baseline policy

The baseline agent receives an `Observation`, not the environment or complete maze graph. It filters visible doors using the room instruction, then applies a fixed tie-break: **blue → green → red → other colours alphabetically**, followed by door ID. If no door satisfies the rule, or the game is already over, it returns a no-move decision.

Example usage:

```python
from agents.rule_first import RuleFirstAgent
from maze.environment import PerceptaMaze

# Given an initialized PerceptaMaze instance named `maze`:
agent = RuleFirstAgent()
decision = agent.choose_door(maze.observe())
if decision.has_move:
    result = maze.step(decision.door_id)
else:
    print(decision.reason)
```

## Memory-based planning agent

`agents/planning_agent.py` implements `PlanningAgent`. Unlike the rule-first baseline, it keeps per-episode memory of rooms visited and doors observed. It still receives only the current `Observation`; it cannot inspect the hidden environment graph. Its policy is:

1. Filter doors to those that satisfy the current room instruction.
2. Prefer a rule-compliant door leading to an unvisited room.
3. If all immediately legal destinations have been visited, estimate routes to known rooms with unexplored legal exits using breadth-first search over the discovered map.
4. Use destination and door IDs as deterministic tie-breakers.

Memory is specific to one episode. Call `agent.reset()` before reusing an agent for a new maze. Because the maze is partially observable and backtracking is forbidden, the planner is a heuristic exploration policy, not a guarantee of finding the exit or avoiding every dead end.

Example:

```python
from agents.planning_agent import PlanningAgent

agent = PlanningAgent()
observation = maze.observe()
decision = agent.choose_door(observation)
if decision.has_move:
    result = maze.step(decision.door_id)
```

## Simulated colour-perception model

`agents/color_perception.py` provides `ColorPerceptionModel` with two modes:

- `PerceptionMode.NORMAL`: preserves the observation unchanged.
- `PerceptionMode.RED_GREEN_AMBIGUOUS`: maps both red and green labels to the same perceived label (`red-green ambiguous`) while leaving blue distinct.

Example:

```python
from agents.color_perception import ColorPerceptionModel

real_observation = maze.observe()
perceived_observation = ColorPerceptionModel().transform(real_observation)
decision = agent.choose_door(perceived_observation)
```

This is a deliberately simplified, configurable game abstraction. It is **not** a clinical model and does not claim to represent every person with red–green colour vision deficiency. The environment still validates the selected door against the true room rule, so a perceptual ambiguity can lead to a choice that the real environment rejects.

## Run tests

Requires Python 3.10 or newer. No third-party packages are needed for the environment tests.

```bash
python -m unittest discover -s tests -v
```

## Evaluation metrics (Step 5)

`evaluation/runner.py` compares the rule-first baseline and memory-based planner on the same five fixed, hand-authored scenarios. It records per-episode outcomes and aggregate metrics without passing the hidden room graph to either agent.

Run the default evaluation from the project root:

```bash
python -m evaluation.runner
```

To test the simplified red–green ambiguity model:

```bash
python -m evaluation.runner --perception red_green_ambiguous
```

Results are written to `results/episode_results.csv` (one row per agent/scenario) and `results/summary.json` (aggregate metrics). The summary includes:

- **Win rate:** percentage of episodes reaching the exit.
- **Mean moves:** average successful moves per episode, including episodes that end in a loss.
- **Rule compliance:** compliant moves divided by all attempted actions. Invalid choices count against compliance.
- **Dead-end losses** and **no-legal-move losses:** separate counts of these terminal outcomes.
- **Invalid attempts:** choices that are unavailable, violate the true rule, or fail to select a move when a legal move exists.

The batch runner treats an invalid action as a failed episode so evaluations terminate consistently. In the interactive environment, an invalid action is rejected without moving the player. The benchmark is deliberately small and handcrafted for checking the implementation; results such as a win-rate difference over five scenarios are illustrative, **not statistically significant research evidence**. For a paper, expand the suite with many generated mazes, report the number of episodes, and compare agents on identical seeds.

## Planned milestones

- [x] Define core environment and rules
- [x] Add initial unit tests
- [x] Add deterministic rule-first baseline agent
- [x] Add configurable colour-perception simulation
- [x] Add memory-based planning agent
- [x] Add evaluation metrics
- [x] Build Streamlit interface
- [ ] Deploy to Streamlit Community Cloud


## Interactive Streamlit app (Step 6)

Install dependencies and launch the interface from the project root:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

The app supports manual play, the rule-first baseline, and the memory-based planning agent. Select one of the fixed benchmark scenarios or the full 4×4 grid maze (`four_by_four`) and switch between normal colour labels and the simplified red–green ambiguity mode. The current room, instruction, perceived door labels, path history, and agent reasoning are shown without passing the hidden maze graph to the agent. The benchmark panel can run the evaluation suite for the selected perception mode.

For deployment, push the project to GitHub and create a Streamlit Community Cloud app with `app.py` as the main file. The `requirements.txt` file lists Streamlit as the UI dependency; core environment and test code use the Python standard library.
