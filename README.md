# PerceptaMaze

PerceptaMaze is a partially observable, tree-based decision game about rule-following, colour perception, route planning, and repeated exploration. The only winning condition is reaching the single Gold exit in a scenario. Ordinary exits end a run but do not count as wins.

## Current mechanics

- Two fixed scenarios built as rooted trees.
- Every decision room has exactly three outgoing doors.
- Door colours come from red, blue, green, yellow, white, orange, and purple.
- Room instructions vary between `CHOOSE COLOUR` and `AVOID COLOUR`.
- Each scenario contains exactly one Gold exit; all other terminal rooms are ordinary exits.
- If a `CHOOSE` target is absent, the baseline uses a deterministic fixed door-order fallback.
- In selected Gold-route rooms, a red/green counterpart is explicitly accepted by the game rule. These are marked internally and tested.
- Red–green ambiguity is a simplified game abstraction, not a clinical model of colour-vision deficiency.
- Agents receive only current-room observations. The complete tree is held by the environment; the UI map reveals the visited rooms and outgoing doors from those rooms. Developer view can reveal the complete tree and Gold location.

## Agents and AI concepts

1. **Rule-first baseline** — deterministic rule following with fixed door-order fallback.
2. **Memory-based planning agent** — records observations and uses a repeatable rule-driven route choice.
3. **Gold Hunter** — performs up to ten attempts, records failed route histories, and systematically tests route signatures across attempts.

The project demonstrates rule-based reasoning, partial observability, perceptual abstraction, deterministic policies, agent memory, bounded search, and empirical evaluation. The agents are symbolic/rule-based systems, not neural-network models.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m streamlit run app.py
```

## Gameplay

1. Choose Scenario 1 or Scenario 2.
2. Select manual play or one of the three agents.
3. Select normal vision or simulated red–green ambiguity.
4. Move through the tree. The bird's-eye map highlights the current room, visited rooms, and colour-coded outgoing doors from rooms already visited.
5. For Gold Hunter, click **Run next Gold Hunter attempt** repeatedly. It keeps attempt memory and stops when Gold is found or ten attempts are exhausted.
6. Reaching an ordinary exit ends that attempt; only the Gold exit is a win.

Use **Developer view** to reveal the complete tree and Gold location for debugging. Keep it off for normal gameplay to preserve partial observability.

## Evaluate

Normal perception:

```powershell
python -m evaluation.runner
```

Red–green ambiguity:

```powershell
python -m evaluation.runner --perception red_green_ambiguous
```

Results are written to `results/episode_results.csv` and `results/summary.json`. The included scenarios are small and handcrafted, so treat results as functional checks rather than statistically strong research evidence. For a paper, evaluate many independently designed trees and report aggregate results across seeds.

## Git workflow

Commit your changes from your existing repository; do not replace its `.git` folder with a downloaded archive.
