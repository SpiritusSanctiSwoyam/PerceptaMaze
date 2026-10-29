# PerceptaMaze

<p align="center">
  <strong>A partially observable, colour-based AI decision maze</strong><br>
  Explore how rules, perception, memory, and search strategies affect an agent's path to the Gold exit.
</p>

<p align="center">
  <a href="https://perceptamaze-odaugoi6u9ldogjno4wnxl.streamlit.app/"><strong>▶ Play PerceptaMaze</strong></a>
</p>

---

## Overview

**PerceptaMaze** is an interactive AI game and research prototype in which a player or software agent navigates a rooted tree of rooms. Each decision room presents three coloured doors and an instruction such as `CHOOSE BLUE` or `AVOID RED`. The agent must interpret the instruction, use the information it can observe, choose a door, and try to reach the **single Gold exit**.

Ordinary exits end an attempt but **do not count as a win**. This distinction lets the project compare different decision strategies against the same objective.

The project is built with Python and Streamlit. It combines a small game environment, explicit symbolic rules, a perception layer, three agent policies, a tree visualization, and an evaluation runner.

> **Project status:** Working prototype deployed on Streamlit Community Cloud. The supplied scenarios are handcrafted and intentionally small; the current benchmark is useful for functional comparisons, not for making broad statistical claims.

## Inspiration

PerceptaMaze takes conceptual inspiration from the **Shrine of Choosing** described by the user from *The Apothecary Diaries* (Season 2, Episode 7): a historical, escape-room-like test involving coloured doors and instructions that guide a person through a sequence of choices.

PerceptaMaze reimagines that broad premise as an independent AI experiment about decision-making under limited observation and altered colour perception. The game's tree structure, rules, agents, code, and evaluation are its own implementation.

*PerceptaMaze is a fan-inspired, independent project and is not affiliated with or endorsed by the creators, publishers, or rights holders of The Apothecary Diaries.*

## Play online

**Live application:**  
https://perceptamaze-odaugoi6u9ldogjno4wnxl.streamlit.app/

The application is hosted on Streamlit Community Cloud. The deployed version reflects the code and dependencies configured for that deployment.

## Game mechanics

- **Rooted tree:** The maze is represented as a branching tree rather than a grid.
- **Three choices per decision room:** Each decision room has exactly three outgoing doors.
- **Seven door colours:** Red, blue, green, yellow, white, orange, and purple.
- **Room instructions:** Rooms use `CHOOSE COLOUR` or `AVOID COLOUR` rules.
- **One Gold exit per scenario:** Gold is the only winning destination. Ordinary exits terminate an attempt without a win.
- **Deterministic fallback:** If a `CHOOSE` target is absent, the baseline policy follows a fixed door-order fallback.
- **Designed red/green equivalence:** Selected rooms explicitly allow a red/green counterpart as part of the game rules. This is a scenario mechanic, not a general property of colour perception.
- **Partial observations:** Agents receive information about their current room, not the complete hidden tree. The environment stores the full maze.
- **Developer view:** An optional debugging view can reveal the full tree and Gold location. Keep it disabled during normal play if you want to preserve the partial-observability setup.

### Perception modes

1. **Normal vision** — red and green are treated as distinct perceived colours.
2. **Red–green ambiguity** — the perception layer maps red and green to a shared game category.

The second mode is a simplified experimental abstraction. It is **not** a clinical or physiological simulation of colour-vision deficiency, and it should not be interpreted as representing every person's perception.

## The three agents

| Agent | Strategy | What it demonstrates | Current limitation |
|---|---|---|---|
| **Rule-first baseline** | Applies the room instruction and uses a deterministic fallback when needed. | Explicit rules, deterministic policies, and a baseline for comparison. | Does not plan a complete route to Gold or learn from failed episodes. |
| **Memory-based planning agent** | Records observed rooms and doors, then prefers a candidate leading to an unvisited room. | Internal state, memory, and history-informed heuristic decisions. | It is a lightweight heuristic policy, not a classical BFS, DFS, or A* pathfinder. |
| **Gold Hunter** | Tries a predetermined sequence of door-index routes over up to ten attempts and records route history. | Bounded repeated attempts, route tracking, and goal-based stopping. | The route order is predetermined; recorded history does not currently adapt the next route choice. |

All three agents are **symbolic/rule-based programs**. They do not train a neural network or learn parameters from a dataset. The current Gold Hunter interface requires the user to start each attempt separately; the evaluation runner can loop over attempts automatically.

## AI concepts in the project

| Concept | How it appears in PerceptaMaze |
|---|---|
| **Rule-based reasoning** | Agents interpret `CHOOSE` and `AVOID` instructions using explicit logic. |
| **Agent–environment interaction** | An agent selects a door; the environment executes the move and determines the outcome. |
| **Partial observability** | The agent receives the current room's observation instead of the complete maze. |
| **Perceptual abstraction** | A configurable layer transforms the perceived colours before the agent makes its decision. |
| **Deterministic decision-making** | Given the same observation and state, an agent follows a repeatable policy. |
| **Internal state and memory** | Planning and Gold Hunter agents retain information about visited rooms or attempts. |
| **Heuristic exploration** | The planning agent prefers destinations it has not visited. |
| **Bounded search / repeated attempts** | Gold Hunter is limited to ten attempts. |
| **Empirical evaluation** | The evaluation runner records episode outcomes and summarizes agent performance. |

### What the project does not currently claim

PerceptaMaze does not currently implement supervised machine learning, reinforcement learning, neural networks, Bayesian reasoning, or a general-purpose shortest-path algorithm. Gold Hunter's route history is recorded, but its next route is selected by a predetermined sequence rather than an adaptive learning algorithm.

These distinctions are important when describing the project in a report, presentation, or research paper.

## How a turn works

1. The environment exposes an observation of the current room.
2. The selected perception mode transforms the observed colours, if applicable.
3. The chosen agent evaluates the instruction and available doors.
4. The agent returns a door choice and an explanation.
5. The environment validates the choice, moves the player/agent, and updates the episode state.
6. The environment checks whether the destination is Gold, an ordinary exit, or another decision room.
7. The interface updates the move log and tree visualization.

The separation between **observation**, **decision**, and **environment transition** makes it possible to compare agents under shared game rules.

## Repository structure

```text
PerceptaMaze/
├── app.py                       # Streamlit UI, session state, gameplay, visualization
├── app_scenarios.py              # Fixed scenario and tree definitions
├── requirements.txt              # Python package dependencies
├── agents/
│   ├── base_agent.py             # Shared agent interface and decision structure
│   ├── rule_first.py             # Rule-first baseline
│   ├── planning_agent.py         # Memory-based heuristic agent
│   ├── gold_hunter.py            # Bounded repeated-attempt agent
│   └── color_perception.py       # Perception-mode transformation
├── maze/
│   ├── environment.py            # Maze state, observations, moves, outcomes
│   └── rules.py                  # CHOOSE/AVOID rule handling
├── evaluation/
│   └── runner.py                 # Episode execution, benchmark and summaries
├── tests/
│   ├── test_environment.py
│   ├── test_app_scenarios.py
│   ├── test_color_perception.py
│   ├── test_rule_first_agent.py
│   ├── test_planning_agent.py
│   └── test_evaluation.py
└── results/                      # Generated evaluation output (if retained locally)
```

`results/` is generated output and may be excluded from version control by `.gitignore`. If code or scenarios change, regenerate the results before using them in a report.

## Run locally

### Requirements

- Python 3.10 or newer
- `pip`
- Git (optional, for cloning and version control)

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd PerceptaMaze
```

Replace `<YOUR_GITHUB_REPOSITORY_URL>` with the URL of your GitHub repository.

### 2. Create and activate a virtual environment

**Windows PowerShell**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Run the tests

```bash
python -m unittest discover -s tests -v
```

A successful run should report that the tests pass. If a test fails, review the traceback before treating a benchmark result as valid.

### 5. Launch the app

```bash
python -m streamlit run app.py
```

Streamlit will print a local address, typically `http://localhost:8501`, where the application can be opened in a browser.

## How to play

1. Open the app and choose one of the available scenarios.
2. Select an agent or use manual play.
3. Choose **Normal vision** or **Red–green ambiguity**.
4. Follow the current room's instruction and select a door.
5. Use the tree view to inspect the current room, visited rooms, and observed branches.
6. If debugging, enable **Developer view** to inspect hidden maze structure and the Gold location.
7. With Gold Hunter, select **Run next Gold Hunter attempt** to run an attempt. Start further attempts manually if necessary.
8. Reach the Gold exit to win. Reaching an ordinary exit ends the attempt without a win.

For a fair partial-observability demonstration, leave Developer view off during gameplay.

## Run the evaluation

Evaluate the default perception mode:

```bash
python -m evaluation.runner
```

Evaluate the red–green-ambiguity mode:

```bash
python -m evaluation.runner --perception red_green_ambiguous
```

The evaluation runner executes agents against the supplied scenarios and writes result summaries to the configured `results/` directory, including episode-level CSV output and a JSON summary.

### Interpreting results responsibly

The built-in scenarios are small and handcrafted. They are appropriate for checking mechanics and illustrating how a particular policy behaves in the designed cases, but they are not enough to establish general agent superiority or a general benefit from red–green ambiguity.

For a stronger study:

- evaluate many independently generated maze trees;
- record and publish the random seeds and configuration;
- compare agents on the same scenarios;
- report Gold success rate, attempts to Gold, moves, and invalid actions;
- separate results by perception mode;
- report the number of trials and uncertainty, not only a percentage;
- regenerate results after every relevant code or scenario change.

## Deployment

The application is deployed on Streamlit Community Cloud:

https://perceptamaze-odaugoi6u9ldogjno4wnxl.streamlit.app/

For future releases, push the intended commit to the connected GitHub branch and confirm that the Streamlit deployment finishes rebuilding. Then test the live app in a private/incognito browser window and check both gameplay and the application logs if something fails.

## Current limitations and possible next steps

Potential development priorities include:

1. **Adaptive Gold Hunter:** use route history to choose unexplored alternatives instead of following a fixed sequence.
2. **Run Full Hunt UI:** add an option that automatically repeats attempts until Gold is found or the ten-attempt limit is reached.
3. **Generalized maze generation:** test different tree depths, branching layouts, door orders, and Gold positions.
4. **Stronger partial-observability tests:** ensure that decision-making agents cannot inspect hidden Gold locations or the full graph.
5. **Reproducible evaluation:** add configurable random seeds, more trials, aggregate metrics, and clear result versioning.
6. **Research reporting:** document methodology, limitations, and results without overgeneralizing from the two supplied scenarios.

## Contributing and version control

Keep changes in small, descriptive commits. Run the test suite before committing, and avoid committing virtual environments, secrets, or stale generated results.

Example:

```bash
git status
python -m unittest discover -s tests -v
git add README.md
git commit -m "Improve project documentation"
git push
```

If your working branch differs from the branch connected to Streamlit Community Cloud, verify the deployment branch before expecting the live app to update.

## Acknowledgements

Inspired by the coloured-door, instruction-driven shrine test described in *The Apothecary Diaries*. This project independently explores the idea through a small AI decision environment.

---

**PerceptaMaze** — a small environment for exploring how rules, perception, and limited information shape decisions.
