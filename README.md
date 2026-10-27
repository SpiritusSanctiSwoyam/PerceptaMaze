# PerceptaMaze

PerceptaMaze is an AI maze game prototype in which an agent sees only its current room, reads a colour-based instruction, and chooses one of the available doors. The project will compare simple rule-following agents with an AI planning agent.

## Current status

The first milestone implements the environment, explicit room rules, partial observations, no-backtracking enforcement, terminal outcomes, and unit tests. The Streamlit interface and agent policies will be added in later milestones.

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

## Run tests

Requires Python 3.10 or newer. No third-party packages are needed for the environment tests.

```bash
python -m unittest discover -s tests -v
```

## Planned milestones

- [x] Define core environment and rules
- [x] Add initial unit tests
- [ ] Add deterministic rule-first baseline agent
- [ ] Add configurable colour-perception simulation
- [ ] Add planning agent and evaluation metrics
- [ ] Build Streamlit interface
- [ ] Deploy to Streamlit Community Cloud
