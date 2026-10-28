"""Streamlit interface for the partially observable PerceptaMaze game."""

from __future__ import annotations

import streamlit as st

from agents.base_agent import BaseAgent
from app_scenarios import interactive_scenarios
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from agents.planning_agent import PlanningAgent
from agents.rule_first import RuleFirstAgent
from evaluation.runner import evaluate_agents, scenario_suite, summarise
from maze.environment import GameStatus, InvalidMove, PerceptaMaze
from maze.rules import rule_compliant_doors


AGENT_FACTORIES = {
    "Manual play": None,
    RuleFirstAgent.name: RuleFirstAgent,
    PlanningAgent.name: PlanningAgent,
}


def new_agent(agent_name: str) -> BaseAgent | None:
    factory = AGENT_FACTORIES[agent_name]
    return factory() if factory else None


def reset_episode(scenario_name: str, agent_name: str, perception_name: str) -> None:
    scenario = next(s for s in interactive_scenarios() if s.name == scenario_name)
    st.session_state.maze = scenario.create_maze()
    st.session_state.action_log = []
    st.session_state.last_message = "New episode started."
    st.session_state.agent = new_agent(agent_name)
    st.session_state.active_scenario = scenario_name
    st.session_state.active_agent = agent_name
    st.session_state.active_perception = perception_name


def get_perception(mode_name: str) -> ColorPerceptionModel | None:
    if mode_name == PerceptionMode.NORMAL.value:
        return None
    return ColorPerceptionModel(PerceptionMode(mode_name))


def perceived_observation(maze: PerceptaMaze, mode_name: str):
    observation = maze.observe()
    model = get_perception(mode_name)
    return model.transform(observation) if model else observation


def apply_move(door_id: str, label: str, reason: str = "") -> None:
    maze = st.session_state.maze
    try:
        result = maze.step(door_id)
        entry = f"{len(st.session_state.action_log) + 1}. {label}: {door_id} — {result.message}"
        if reason:
            entry += f"\n   Agent reasoning: {reason}"
        st.session_state.action_log.append(entry)
        st.session_state.last_message = result.message
    except InvalidMove as exc:
        st.session_state.last_message = f"Move rejected: {exc}"
        st.session_state.action_log.append(f"Rejected attempt: {door_id} — {exc}")


def main() -> None:
    st.set_page_config(page_title="PerceptaMaze", page_icon="🧩", layout="wide")
    st.title("🧩 PerceptaMaze")
    st.caption("A partially observable maze about rule-following, exploration, and colour-perception ambiguity.")

    with st.sidebar:
        st.header("Game setup")
        scenarios = interactive_scenarios()
        scenario_labels = {s.name: f"{s.name.replace('_', ' ').title()} — {s.description}" for s in scenarios}
        scenario_name = st.selectbox("Maze scenario", options=list(scenario_labels), format_func=lambda key: scenario_labels[key])
        agent_name = st.selectbox("How should decisions be made?", options=list(AGENT_FACTORIES))
        perception_name = st.selectbox(
            "Perception mode",
            options=[PerceptionMode.NORMAL.value, PerceptionMode.RED_GREEN_AMBIGUOUS.value],
            format_func=lambda value: "Normal colours" if value == "normal" else "Simulated red–green ambiguity",
            help="This is a simplified game abstraction, not a clinical model of colour vision deficiency.",
        )
        if st.button("↻ Restart episode", use_container_width=True):
            reset_episode(scenario_name, agent_name, perception_name)
            st.rerun()

    if "maze" not in st.session_state:
        reset_episode(scenario_name, agent_name, perception_name)
    elif (
        st.session_state.active_scenario != scenario_name
        or st.session_state.active_agent != agent_name
        or st.session_state.active_perception != perception_name
    ):
        reset_episode(scenario_name, agent_name, perception_name)

    maze: PerceptaMaze = st.session_state.maze
    observation = perceived_observation(maze, perception_name)
    true_observation = maze.observe()

    status_col, room_col, moves_col = st.columns(3)
    status_col.metric("Game status", maze.status.value.upper())
    room_col.metric("Current room", true_observation.room_id)
    moves_col.metric("Rooms visited", len(maze.history))

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        st.subheader("Current room")
        st.info(f"**Room {observation.room_id}**  \nInstruction: **{observation.rule_text}**")
        st.caption("Only the current room is shown to the player/agent. The full maze graph remains hidden.")

        if maze.status is GameStatus.WON:
            st.success("🏆 You reached the exit. You win!")
        elif maze.status is GameStatus.LOST:
            st.error("Game over. " + st.session_state.last_message)
        elif not rule_compliant_doors(true_observation.doors, true_observation.rule):
            st.warning("No visible door satisfies this room's rule. Press a move button or let the agent act to register the loss.")
            if st.button("Resolve room (no legal door)"):
                result = maze.step("__no_legal_move__")
                st.session_state.last_message = result.message
                st.session_state.action_log.append(result.message)
                st.rerun()
        elif agent_name == "Manual play":
            st.markdown("Choose one of the available doors:")
            for door in observation.doors:
                # Show perceived labels, never the hidden true label in ambiguous mode.
                if st.button(
                    f"🚪 {door.door_id}  ·  perceived colour: {door.color}  ·  to {door.destination}",
                    key=f"manual_{len(maze.history)}_{door.door_id}",
                    use_container_width=True,
                ):
                    apply_move(door.door_id, "Player")
                    st.rerun()
        else:
            st.write(f"Active agent: **{agent_name}**")
            if st.button("🤖 Let agent choose and move", type="primary", use_container_width=True):
                agent = st.session_state.agent
                decision = agent.choose_door(observation)
                if not decision.has_move:
                    if not rule_compliant_doors(true_observation.doors, true_observation.rule):
                        result = maze.step("__no_legal_move__")
                        st.session_state.last_message = result.message
                        st.session_state.action_log.append(f"{agent_name}: {result.message}")
                    else:
                        st.session_state.last_message = f"Agent did not select a move: {decision.reason}"
                        st.session_state.action_log.append(st.session_state.last_message)
                else:
                    apply_move(decision.door_id, agent_name, decision.reason)
                st.rerun()
            if st.session_state.agent is not None and hasattr(st.session_state.agent, "memory"):
                memory = st.session_state.agent.memory
                st.caption(f"Planner memory: {len(memory.visited_rooms)} room visit(s), {len(memory.known_rooms)} room(s) recorded.")

        st.info(st.session_state.last_message)

    with right:
        st.subheader("Episode details")
        st.write("**Room path:** " + " → ".join(maze.history))
        st.write(f"**Previous room:** {true_observation.previous_room or 'None'}")
        st.write(f"**Available doors:** {len(observation.doors)}")
        if st.session_state.action_log:
            st.markdown("#### Move history")
            for item in reversed(st.session_state.action_log):
                st.markdown(f"- {item}")
        else:
            st.caption("No moves yet. Start by selecting a door or letting the agent act.")

    st.divider()
    st.subheader("Benchmark evaluation")
    st.caption("The benchmark runs agents on fixed scenarios independently of the interactive episode. These small handcrafted results are illustrative, not research-grade statistical evidence.")
    if st.button("Run benchmark for selected perception mode"):
        model = get_perception(perception_name)
        results = evaluate_agents(perception=model)
        st.session_state.benchmark_summary = summarise(results)
        st.session_state.benchmark_mode = perception_name
    if "benchmark_summary" in st.session_state:
        st.caption(f"Last run: {st.session_state.benchmark_mode}")
        st.dataframe(st.session_state.benchmark_summary, use_container_width=True, hide_index=True)

    st.divider()
    st.caption("PerceptaMaze's red–green ambiguity option is a configurable game simulation and should not be interpreted as a medical or clinical representation.")


if __name__ == "__main__":
    main()
