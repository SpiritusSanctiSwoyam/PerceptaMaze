"""Interactive-only scenarios, including a 4x4 grid maze for the UI."""

from __future__ import annotations

from evaluation.runner import Scenario, scenario_suite
from maze.environment import Door, Room
from maze.rules import RoomRule, RuleKind


def four_by_four_scenario() -> Scenario:
    """Create a 4x4 maze with a narrow safe route and off-route dead ends.

    The grid coordinates are used only to build the environment. They are not
    included in observations, so neither agent can inspect the hidden layout.
    """
    exit_coord = (3, 3)
    safe_path = {
        (0, 0), (0, 1), (0, 2), (0, 3), (1, 3), (2, 3), (3, 3)
    }
    rooms: dict[str, Room] = {}

    def room_id(row: int, col: int) -> str:
        return f"R{row}{col}"

    for row in range(4):
        for col in range(4):
            coord = (row, col)
            rid = room_id(row, col)
            if coord == exit_coord:
                rooms[rid] = Room(rid, RoomRule(RuleKind.AVOID, "red"), (), is_exit=True)
                continue

            neighbours: list[tuple[str, tuple[int, int]]] = []
            for label, (dr, dc) in (("N", (-1, 0)), ("E", (0, 1)), ("S", (1, 0)), ("W", (0, -1))):
                nr, nc = row + dr, col + dc
                if 0 <= nr < 4 and 0 <= nc < 4:
                    neighbours.append((label, (nr, nc)))

            # The designated route always uses a blue door. At the start, a
            # green door is also legal, making the first decision meaningful.
            forward: tuple[int, int] | None = None
            if coord == (0, 0):
                forward = (0, 1)
            elif coord in safe_path:
                if row == 0 and col < 3:
                    forward = (0, col + 1)
                elif col == 3 and row < 3:
                    forward = (row + 1, 3)

            doors: list[Door] = []
            for label, dest_coord in neighbours:
                destination = room_id(*dest_coord)
                if dest_coord == forward:
                    color = "blue"
                elif coord == (0, 0) and dest_coord == (1, 0):
                    color = "green"
                else:
                    color = "red" if dest_coord in safe_path else "green"
                doors.append(Door(f"{rid}-{label}", color, destination))

            if coord == (0, 0):
                rule = RoomRule(RuleKind.AVOID, "red")
            elif coord in safe_path:
                rule = RoomRule(RuleKind.CHOOSE, "blue")
            else:
                rule = RoomRule(RuleKind.AVOID, "red")
            rooms[rid] = Room(
                rid,
                rule,
                tuple(doors),
                is_dead_end=coord not in safe_path,
            )

    return Scenario(
        name="four_by_four",
        description="A 4×4 grid maze with a hidden safe route and off-route dead ends.",
        rooms=rooms,
        start_room="R00",
        exit_room="R33",
    )


def interactive_scenarios() -> tuple[Scenario, ...]:
    """Return the benchmark scenarios plus the full 4x4 interactive maze."""
    return (*scenario_suite(), four_by_four_scenario())
