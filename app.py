"""Interactive PerceptaMaze: tree mazes, colour perception, Gold Hunter, live map."""
from __future__ import annotations
import streamlit as st
from agents.base_agent import BaseAgent
from agents.color_perception import ColorPerceptionModel, PerceptionMode
from agents.gold_hunter import GoldHunterAgent
from agents.planning_agent import PlanningAgent
from agents.rule_first import RuleFirstAgent
from app_scenarios import Scenario, interactive_scenarios
from evaluation.runner import evaluate_agents, summarise
from maze.environment import GameStatus, InvalidMove, PerceptaMaze

AGENTS = {"Manual play": None, RuleFirstAgent.name: RuleFirstAgent, PlanningAgent.name: PlanningAgent, GoldHunterAgent.name: GoldHunterAgent}
COLOR_HEX = {"red":"#d62728", "blue":"#1f77b4", "green":"#2ca02c", "yellow":"#f1c40f", "white":"#ffffff", "orange":"#ff8c00", "purple":"#9467bd", "red-green ambiguous":"#8e6b8e"}


def _scenario(name: str) -> Scenario:
    return next(s for s in interactive_scenarios() if s.name == name)

def _perception(mode: str):
    return None if mode == PerceptionMode.NORMAL.value else ColorPerceptionModel(PerceptionMode(mode))

def _reset(scenario_name: str, agent_name: str, mode: str):
    sc = _scenario(scenario_name)
    st.session_state.scenario = sc
    st.session_state.maze = sc.create_maze()
    st.session_state.agent = AGENTS[agent_name]() if AGENTS[agent_name] else None
    st.session_state.log = []
    st.session_state.message = "New game started. Reach the Gold exit to win."
    st.session_state.attempt_number = 0
    st.session_state.attempts_used = 0
    st.session_state.finished_routes = []
    st.session_state.active_config = (scenario_name, agent_name, mode)

def _map_dot(scenario: Scenario, maze: PerceptaMaze, reveal_all: bool = False) -> str:
    visited = set(maze.history)
    shown = set(scenario.rooms) if reveal_all else set(visited)
    edges = []
    for rid in list(shown):
        room = scenario.rooms[rid]
        for door in room.doors:
            # Only reveal doors of visited rooms; unvisited destination IDs are visible as frontier stubs.
            if reveal_all or rid in visited:
                shown.add(door.destination)
                color = COLOR_HEX.get(door.color, "#666666")
                edges.append(f'"{rid}" -> "{door.destination}" [label="{door.color}", color="{color}", fontcolor="{color}", penwidth=2];')
    lines = ['digraph Maze { rankdir=TB; bgcolor="transparent"; node [shape=box, style="rounded,filled", fontname="Arial", color="#666666"]; edge [fontname="Arial", fontsize=9];']
    for rid in sorted(shown):
        if rid not in scenario.rooms:
            continue
        room = scenario.rooms[rid]
        if rid == maze.current_room:
            fill, border, pen = "#ffe08a", "#d18b00", 3
        elif rid in visited:
            fill, border, pen = "#b9e4c9", "#228b55", 2
        elif room.is_gold_exit and reveal_all:
            fill, border, pen = "#ffd700", "#b8860b", 3
        elif room.is_exit:
            fill, border, pen = "#e8e8e8", "#777777", 1
        else:
            fill, border, pen = "#f4f4f4", "#aaaaaa", 1
        label = rid
        if rid == scenario.start_room: label += "\\nSTART"
        if rid == maze.current_room: label += "\\nCURRENT"
        if room.is_exit and reveal_all: label += "\\nGOLD" if room.is_gold_exit else "\\nExit"
        lines.append(f'"{rid}" [label="{label}", fillcolor="{fill}", color="{border}", penwidth={pen}];')
    lines.extend(edges)
    lines.append("}")
    return "\n".join(lines)

def _run_agent_turn():
    maze = st.session_state.maze
    agent = st.session_state.agent
    if agent is None or maze.status is not GameStatus.RUNNING:
        return
    mode = st.session_state.active_config[2]
    model = _perception(mode)
    true_obs = maze.observe()
    obs = model.transform(true_obs) if model else true_obs
    decision = agent.choose_door(obs)
    if not decision.has_move:
        st.session_state.message = decision.reason
        st.session_state.log.append(decision.reason)
        return
    try:
        result = maze.step(decision.door_id)
        line = f"{len(st.session_state.log)+1}. {true_obs.room_id}: {decision.door_id} → {result.entered_room}. {result.message}"
        line += f" Agent reasoning: {decision.reason}"
        st.session_state.log.append(line)
        st.session_state.message = result.message
    except InvalidMove as exc:
        st.session_state.message = f"Move rejected: {exc}"

def _gold_hunter_attempt():
    agent: GoldHunterAgent = st.session_state.agent
    if st.session_state.attempts_used >= agent.MAX_ATTEMPTS or st.session_state.maze.status is GameStatus.WON:
        return
    if st.session_state.attempt_number == 0 or st.session_state.maze.status is not GameStatus.RUNNING:
        st.session_state.maze = st.session_state.scenario.create_maze()
        agent.begin_attempt()
        st.session_state.attempt_number += 1
        st.session_state.attempts_used += 1
    start_len = len(st.session_state.log)
    for _ in range(3):
        if st.session_state.maze.status is not GameStatus.RUNNING:
            break
        _run_agent_turn()
    won = st.session_state.maze.status is GameStatus.WON
    agent.finish_attempt(won)
    route = tuple(st.session_state.maze.history)
    st.session_state.finished_routes.append(route)
    if won:
        st.session_state.message = f"🏆 Gold Hunter found Gold on attempt {st.session_state.attempts_used}!"
    elif st.session_state.attempts_used >= agent.MAX_ATTEMPTS:
        st.session_state.message = "Attempt limit reached. Gold was not found in this hunt. Restart to try again."
    else:
        st.session_state.message = f"Attempt {st.session_state.attempts_used} ended at an ordinary exit. Knowledge retained; try another route."


def main():
    st.set_page_config(page_title="PerceptaMaze", page_icon="🧩", layout="wide")
    st.title("🧩 PerceptaMaze")
    st.caption("A partially observable tree-maze exploring rule-based reasoning, colour perception, route search, and Gold acquisition.")
    with st.sidebar:
        st.header("Game setup")
        scenarios = interactive_scenarios()
        scenario_name = st.selectbox("Maze scenario", [s.name for s in scenarios], format_func=lambda n: f"{n.replace('_',' ').title()} — fixed tree")
        agent_name = st.selectbox("Agent", list(AGENTS))
        mode = st.selectbox("Perception", [m.value for m in PerceptionMode], format_func=lambda x: "Normal vision" if x == "normal" else "Red–green ambiguity", help="Simplified game abstraction, not a clinical model.")
        reveal = st.checkbox("Developer view: reveal complete tree and Gold location", value=False)
        if st.button("↻ Restart game", use_container_width=True):
            _reset(scenario_name, agent_name, mode)
            st.rerun()
    config = (scenario_name, agent_name, mode)
    if "active_config" not in st.session_state or st.session_state.active_config != config:
        _reset(*config)
    scenario: Scenario = st.session_state.scenario
    maze: PerceptaMaze = st.session_state.maze
    true_obs = maze.observe()
    model = _perception(mode)
    obs = model.transform(true_obs) if model else true_obs

    a, b, c, d = st.columns(4)
    a.metric("Outcome", "GOLD!" if maze.status is GameStatus.WON else ("Ordinary exit" if maze.status is GameStatus.EXITED else "In progress"))
    b.metric("Current room", maze.current_room)
    c.metric("Moves this run", max(0, len(maze.history)-1))
    d.metric("Hunter attempts", f"{st.session_state.attempts_used}/10" if isinstance(st.session_state.agent, GoldHunterAgent) else "—")

    left, right = st.columns([1.0, 1.15], gap="large")
    with left:
        st.subheader("Current room")
        st.info(f"**{obs.room_id}**  ·  Rule: **{obs.rule_text}**")
        st.caption("Three doors are available in every decision room. Door IDs and destinations are shown; unseen room rules remain hidden.")
        if maze.status is GameStatus.WON:
            st.success("🏆 GOLD FOUND — you win!")
        elif maze.status is GameStatus.EXITED:
            st.warning("Ordinary exit reached. Escaping alone is not a win; Gold is the winning condition.")
        elif agent_name == "Manual play":
            for door in obs.doors:
                color = door.color
                label = f"🚪 {door.door_id} · {color.upper()} · next room {door.destination}"
                if st.button(label, key=f"manual_{len(maze.history)}_{door.door_id}", use_container_width=True):
                    try:
                        result = maze.step(door.door_id)
                        st.session_state.message = result.message
                        st.session_state.log.append(f"{true_obs.room_id} — {door.door_id} ({color}) → {result.entered_room}: {result.message}")
                    except InvalidMove as exc:
                        st.session_state.message = str(exc)
                    st.rerun()
        elif isinstance(st.session_state.agent, GoldHunterAgent):
            st.write("Gold Hunter tests a different route on each attempt and remembers the routes it has tried.")
            disabled = st.session_state.attempts_used >= 10 or maze.status is GameStatus.WON
            if st.button("🪙 Run next Gold Hunter attempt", type="primary", disabled=disabled, use_container_width=True):
                _gold_hunter_attempt()
                st.rerun()
        else:
            if st.button("🤖 Let agent choose and move", type="primary", use_container_width=True):
                _run_agent_turn()
                st.rerun()
        st.info(st.session_state.get("message", "Choose a door or let the agent act."))
        if st.session_state.log:
            st.markdown("#### Move history")
            for item in reversed(st.session_state.log[-15:]):
                st.markdown(f"- {item}")

    with right:
        st.subheader("Bird's-eye tree map")
        st.caption("Visited rooms are green, the current room is gold-highlighted, and door labels use their colours. Unvisited room rules remain hidden.")
        st.graphviz_chart(_map_dot(scenario, maze, reveal_all=reveal), use_container_width=True)
        st.markdown("**Room path:** " + " → ".join(maze.history))
        if isinstance(st.session_state.agent, PlanningAgent):
            st.caption(f"Planning memory: {len(st.session_state.agent.memory.visited_rooms)} room visits recorded.")
        if isinstance(st.session_state.agent, GoldHunterAgent):
            st.caption(f"Completed attempts: {len(st.session_state.agent.memory.route_history)}. Each failed attempt is retained in memory.")
            if st.session_state.finished_routes:
                with st.expander("Previous Gold Hunter attempts"):
                    for number, route in enumerate(st.session_state.finished_routes, start=1):
                        st.write(f"Attempt {number}: " + " → ".join(route))

    st.divider()
    st.subheader("Benchmark evaluation")
    st.caption("Gold acquisition is the only winning criterion. Gold Hunter may use up to ten attempts; other agents are measured on a single run per scenario.")
    if st.button("Run benchmark for selected perception"):
        results = evaluate_agents(perception=model)
        st.session_state.benchmark = summarise(results)
    if "benchmark" in st.session_state:
        st.dataframe(st.session_state.benchmark, use_container_width=True, hide_index=True)
    st.caption("PerceptaMaze's red–green ambiguity is a designed game abstraction, not a clinical simulation of colour vision deficiency.")

if __name__ == "__main__":
    main()
