# PerceptaMaze

PerceptaMaze is an AI maze game prototype in which an agent sees only its current room, reads a colour-based instruction, and chooses one of the available doors. The project will compare simple rule-following agents with an AI planning agent.

## Current status

The environment, deterministic rule-first baseline agent, and configurable simulated colour-perception model are implemented. The engine enforces room instructions, partial observations, no-backtracking, dead-end losses, and exit wins. Nineteen unit tests currently pass. The Streamlit interface and planning agent remain future milestones.

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

## Planned milestones

- [x] Define core environment and rules
- [x] Add initial unit tests
- [x] Add deterministic rule-first baseline agent
- [x] Add configurable colour-perception simulation
- [ ] Add planning agent and evaluation metrics
- [ ] Build Streamlit interface
- [ ] Deploy to Streamlit Community Cloud
