"""Two fixed three-door tree scenarios with one Gold leaf each."""
from dataclasses import dataclass
from typing import Mapping
from maze.environment import Door, PerceptaMaze, Room
from maze.rules import RoomRule, RuleKind

PALETTE = ("red", "blue", "green", "yellow", "white", "orange", "purple")

@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    rooms: Mapping[str, Room]
    start_room: str
    gold_room: str
    def create_maze(self) -> PerceptaMaze:
        return PerceptaMaze(self.rooms, self.start_room, self.gold_room)


def _build_scenario(name: str, variant: int) -> Scenario:
    rooms: dict[str, Room] = {}
    gold_route = {"S": 1, "B": (0 if variant == 1 else 1), "B1" if variant == 1 else "B2": 0}
    # Rule/colour configurations are deliberately varied. The Gold path has a
    # single red/green-equivalent target in each relevant room, never both red
    # and green doors together, so the ambiguity-mode agent is not split between them.
    root_colors = ["blue", "green", "yellow"] if variant == 1 else ["yellow", "green", "purple"]
    root_rule = RoomRule(RuleKind.CHOOSE, "red")
    rooms["S"] = Room("S", root_rule, tuple(Door(f"S-{i}", color, dest) for i, (color, dest) in enumerate(zip(root_colors, ("A", "B", "C")))), red_green_equivalence=True)
    level1_rules = [
        RoomRule(RuleKind.AVOID, "orange"),
        RoomRule(RuleKind.AVOID, "green"),
        RoomRule(RuleKind.CHOOSE, "purple"),
    ]
    level1_colors = [
        ["orange", "red", "blue"],
        ["blue", "red", "yellow"] if variant == 1 else ["yellow", "blue", "red"],
        ["purple", "white", "orange"],
    ]
    for i, node in enumerate(("A", "B", "C")):
        children = [f"{node}{j}" for j in (1, 2, 3)]
        rooms[node] = Room(node, level1_rules[i], tuple(Door(f"{node}-{j}", color, dest) for j, (color, dest) in enumerate(zip(level1_colors[i], children))), red_green_equivalence=(node == "B" and variant == 2))
    level2_rules = [
        RoomRule(RuleKind.CHOOSE, "yellow"), RoomRule(RuleKind.CHOOSE, "green"), RoomRule(RuleKind.AVOID, "blue"),
        RoomRule(RuleKind.AVOID, "red"), RoomRule(RuleKind.CHOOSE, "orange"), RoomRule(RuleKind.AVOID, "purple"),
        RoomRule(RuleKind.CHOOSE, "white"), RoomRule(RuleKind.AVOID, "yellow"), RoomRule(RuleKind.CHOOSE, "blue"),
    ]
    level2_colors = [
        ["yellow", "red", "blue"], ["red", "white", "purple"], ["blue", "orange", "green"],
        ["green", "yellow", "orange"], ["orange", "blue", "white"], ["red", "green", "purple"],
        ["white", "blue", "red"], ["yellow", "orange", "green"], ["blue", "purple", "white"],
    ]
    node_ids = [f"{parent}{j}" for parent in ("A", "B", "C") for j in (1, 2, 3)]
    # Ensure the Gold branch's second and third decisions benefit from the
    # perception mapping but remain unambiguous: only one member of red/green is present.
    if variant == 1:
        level2_rules[3] = RoomRule(RuleKind.CHOOSE, "green")
        level2_colors[3] = ["red", "white", "purple"]
    else:
        level2_rules[4] = RoomRule(RuleKind.CHOOSE, "green")
        level2_colors[4] = ["red", "blue", "white"]
    for idx, node in enumerate(node_ids):
        children = [f"{node}x{j}" for j in (1, 2, 3)]
        is_gold_parent = node == ("B1" if variant == 1 else "B2")
        if is_gold_parent:
            # Scenario 1: Gold is door 1 (red) after CHOOSE GREEN.
            # Scenario 2: Gold is also door 1 (red) after CHOOSE GREEN.
            rule = RoomRule(RuleKind.CHOOSE, "green")
            colors = ["red", "white", "purple"]
            rooms[node] = Room(node, rule, tuple(Door(f"{node}-{j}", color, dest) for j, (color, dest) in enumerate(zip(colors, children))), red_green_equivalence=True)
        else:
            rooms[node] = Room(node, level2_rules[idx], tuple(Door(f"{node}-{j}", color, dest) for j, (color, dest) in enumerate(zip(level2_colors[idx], children))))
    gold_room = "B1x1" if variant == 1 else "B2x1"
    # Every leaf is an ordinary exit except the one designated Gold exit.
    for parent in node_ids:
        for j in (1, 2, 3):
            rid = f"{parent}x{j}"
            rooms[rid] = Room(rid, RoomRule(RuleKind.AVOID, "purple"), (), is_exit=True, is_gold_exit=(rid == gold_room))
    # Gold path at root is B; scenario-specific child; then first leaf.
    if variant == 1:
        # B's first child B1 is Gold branch; set B door order to blue, red, yellow;
        # ambiguous AVOID GREEN avoids red and selects blue first -> B1.
        rooms["B"] = Room("B", RoomRule(RuleKind.AVOID, "green"), (Door("B-0", "blue", "B1"), Door("B-1", "red", "B2"), Door("B-2", "yellow", "B3")))
        rooms["B1"] = Room("B1", RoomRule(RuleKind.CHOOSE, "green"), (Door("B1-0", "red", "B1x1"), Door("B1-1", "white", "B1x2"), Door("B1-2", "purple", "B1x3")), red_green_equivalence=True)
    else:
        rooms["B"] = Room("B", RoomRule(RuleKind.AVOID, "green"), (Door("B-0", "red", "B1"), Door("B-1", "blue", "B2"), Door("B-2", "yellow", "B3")))
        rooms["B2"] = Room("B2", RoomRule(RuleKind.CHOOSE, "green"), (Door("B2-0", "red", "B2x1"), Door("B2-1", "blue", "B2x2"), Door("B2-2", "white", "B2x3")), red_green_equivalence=True)
    return Scenario(name, "Three-door rooted tree; one fixed Gold exit and ordinary exits on other branches.", rooms, "S", gold_room)


def scenario_one() -> Scenario:
    return _build_scenario("scenario_1", 1)

def scenario_two() -> Scenario:
    return _build_scenario("scenario_2", 2)

def interactive_scenarios() -> tuple[Scenario, ...]:
    return (scenario_one(), scenario_two())
