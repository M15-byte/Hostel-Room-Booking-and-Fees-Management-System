"""
hostel.py

Everything to do with the physical layout of the hostel: how many blocks
exist, how many rooms each block has, and how much space is left in a
given room.

The system ships with a predefined default layout (three blocks, 55
beds - see DEFAULT_LAYOUT below), which is what a first run starts from,
as the coursework brief asks. A warden whose building looks different
can replace it with a layout of their own through menu option 10, so
this same code still works for a 20-bed hostel or a 2,000-bed one
without a single line changing.
"""

from typing import Dict
from models import Room

# Type alias so the rest of the codebase doesn't have to spell this out
# every time - a hostel is a mapping of block name -> (room number -> Room).
HostelLayout = Dict[str, Dict[str, Room]]

# The predefined default hostel required by the coursework brief:
# (block name, number of rooms, beds per room). Block A and Block B have
# five 4-bed rooms each, Block C has five 3-bed rooms - 55 beds in total.
DEFAULT_LAYOUT = (
    ("Block A", 5, 4),
    ("Block B", 5, 4),
    ("Block C", 5, 3),
)


def create_default_layout() -> HostelLayout:
    """
    Builds the predefined default hostel from DEFAULT_LAYOUT.

    Room numbers follow their block's letter (A01..A05, B01..B05,
    C01..C05), so a room number can be read as a location at a glance.
    Used automatically whenever the program starts and finds no saved
    data file, meaning the warden never has to answer setup questions
    before the system is usable.
    """
    layout: HostelLayout = {}

    for block_name, number_of_rooms, capacity in DEFAULT_LAYOUT:
        letter = block_name.split()[-1]
        rooms = {
            f"{letter}{index:02d}": Room(capacity=capacity)
            for index in range(1, number_of_rooms + 1)
        }
        layout[block_name] = rooms

    return layout


def ask_positive_int(prompt: str) -> int:
    """
    Repeats a prompt until the user enters a whole number greater than zero.

    Pulled out into its own function because both the block count and the
    room capacity need the exact same validation, and duplicating a
    while-loop in two places is how that validation quietly drifts apart
    over time.
    """
    while True:
        raw_value = input(prompt).strip()
        if not raw_value.isdigit():
            print("Please enter a whole number greater than zero.")
            continue
        value = int(raw_value)
        if value <= 0:
            print("The number must be greater than zero.")
            continue
        return value


def build_hostel_layout() -> HostelLayout:
    """
    Interactively builds a hostel's block/room structure from scratch.

    This is the "custom layout" path behind menu option 10, for wardens
    whose building doesn't match the predefined default. Every block
    name, room number and capacity is typed in by the warden, so the
    structure always matches the real building instead of a guess baked
    into the source code.
    """
    layout: HostelLayout = {}

    print("\nNo existing hostel layout was found - let's set one up.")
    number_of_blocks = ask_positive_int("How many hostel blocks are there? ")

    for block_index in range(1, number_of_blocks + 1):
        block_name = input(f"Name of block {block_index} (e.g. Block A): ").strip()
        while not block_name:
            block_name = input("Block name cannot be empty. Try again: ").strip()

        number_of_rooms = ask_positive_int(f"How many rooms does {block_name} have? ")
        rooms: Dict[str, Room] = {}

        for room_index in range(1, number_of_rooms + 1):
            room_no = input(f"  Room number {room_index} of {block_name}: ").strip()
            while not room_no or room_no in rooms:
                room_no = input("  Room number is empty or already used. Try again: ").strip()

            capacity = ask_positive_int(f"  Capacity of room {room_no}: ")
            rooms[room_no] = Room(capacity=capacity)

        layout[block_name] = rooms

    print("\nHostel layout saved for this session.")
    return layout


def room_exists(layout: HostelLayout, block: str, room_no: str) -> bool:
    return block in layout and room_no in layout[block]


def get_room(layout: HostelLayout, block: str, room_no: str) -> Room:
    """Direct lookup - callers are expected to check room_exists() first."""
    return layout[block][room_no]


def display_occupancy(layout: HostelLayout) -> None:
    """Prints every block and every room's current occupancy in one pass."""
    print("\n========== HOSTEL OCCUPANCY REPORT ==========")
    for block_name, rooms in layout.items():
        print(f"\n{block_name.upper()}")
        for room_no, room in rooms.items():
            print(f"{room_no}: {room.occupancy_label()}")


def add_occupant(layout: HostelLayout, block: str, room_no: str, reg_no: str) -> None:
    room = get_room(layout, block, room_no)
    room.occupants.append(reg_no)


def remove_occupant(layout: HostelLayout, block: str, room_no: str, reg_no: str) -> None:
    room = get_room(layout, block, room_no)
    if reg_no in room.occupants:
        room.occupants.remove(reg_no)


def total_capacity(layout: HostelLayout) -> int:
    """Total number of beds across every block - used for the one-line
    summary written to the activity log every time data is saved."""
    return sum(room.capacity for rooms in layout.values() for room in rooms.values())


def total_occupied(layout: HostelLayout) -> int:
    return sum(len(room.occupants) for rooms in layout.values() for room in rooms.values())
