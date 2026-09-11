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

from typing import Dict, Optional
from models import Room


# A hostel contains blocks, and each block contains rooms.
HostelLayout = Dict[str, Dict[str, Room]]

# Default layout: block name, number of rooms, beds per room.
DEFAULT_LAYOUT = (
    ("Block A", 5, 4),
    ("Block B", 5, 4),
    ("Block C", 5, 3),
)


# Creates the predefined three-block hostel.
def create_default_layout() -> HostelLayout:
    layout: HostelLayout = {}

    for block_name, number_of_rooms, capacity in DEFAULT_LAYOUT:
        letter = block_name.split()[-1]
        rooms = {
            f"{letter}{number:02d}": Room(capacity=capacity)
            for number in range(1, number_of_rooms + 1)
        }
        layout[block_name] = rooms

    return layout


# Repeats a prompt until a positive whole number is entered.
def ask_positive_int(prompt: str) -> int:
    while True:
        raw_value = input(prompt).strip()
        if not raw_value.isdigit():
            print("Please enter a whole number greater than zero.")
            continue

        value = int(raw_value)
        if value == 0:
            print("The number must be greater than zero.")
            continue

        return value


# Checks an exact block and room key without causing a KeyError.
def room_exists(layout: HostelLayout, block: str, room_no: str) -> bool:
    return block in layout and room_no in layout[block]


# Converts block input such as A or block a to the stored block name.
def resolve_block_name(layout: HostelLayout, block: str) -> Optional[str]:
    entered = " ".join(block.strip().split()).casefold()
    if not entered:
        return None

    for stored_name in layout:
        stored = " ".join(stored_name.strip().split()).casefold()
        if stored == entered:
            return stored_name

    entered_short = entered.removeprefix("block ").strip()
    matches = []

    for stored_name in layout:
        stored = " ".join(stored_name.strip().split()).casefold()
        stored_short = stored.removeprefix("block ").strip()
        if stored_short == entered_short:
            matches.append(stored_name)

    if len(matches) == 1:
        return matches[0]
    return None


# Converts room input such as 1 or 01 to the stored room number A01.
def resolve_room_number(
    layout: HostelLayout,
    block: str,
    room_no: str,
) -> Optional[str]:
    if block not in layout:
        return None

    entered = "".join(room_no.strip().split())
    if entered.casefold().startswith("room"):
        entered = entered[4:].lstrip("-:")
    if not entered:
        return None

    rooms = layout[block]

    for stored_room in rooms:
        stored_compact = "".join(stored_room.split())
        if stored_compact.casefold() == entered.casefold():
            return stored_room

    if entered.isdigit():
        wanted_number = int(entered)
        matches = []

        for stored_room in rooms:
            stored_compact = "".join(stored_room.split())
            index = len(stored_compact)
            while index > 0 and stored_compact[index - 1].isdigit():
                index -= 1

            suffix = stored_compact[index:]
            if suffix and int(suffix) == wanted_number:
                matches.append(stored_room)

        if len(matches) == 1:
            return matches[0]

    return None


# Builds a custom hostel layout from validated user input.
def build_hostel_layout() -> HostelLayout:
    layout: HostelLayout = {}

    print("\nCreating a custom hostel layout.")
    number_of_blocks = ask_positive_int("How many hostel blocks are there? ")

    for block_index in range(1, number_of_blocks + 1):
        while True:
            block_name = input(
                f"Name of block {block_index} (e.g. Block A): "
            ).strip()
            block_name = " ".join(block_name.split())

            if not block_name:
                print("Block name cannot be empty.")
            elif resolve_block_name(layout, block_name) is not None:
                print("That block name is already used.")
            else:
                break

        number_of_rooms = ask_positive_int(
            f"How many rooms does {block_name} have? "
        )
        rooms: Dict[str, Room] = {}

        for room_index in range(1, number_of_rooms + 1):
            while True:
                room_no = input(
                    f"  Room number {room_index} of {block_name}: "
                ).strip()
                room_no = " ".join(room_no.split())
                compact = "".join(room_no.split()).casefold()
                duplicate = any(
                    "".join(existing.split()).casefold() == compact
                    for existing in rooms
                )

                if not room_no:
                    print("  Room number cannot be empty.")
                elif duplicate:
                    print("  That room number is already used in this block.")
                else:
                    break

            capacity = ask_positive_int(f"  Capacity of room {room_no}: ")
            rooms[room_no] = Room(capacity=capacity)

        layout[block_name] = rooms

    print("\nCustom hostel layout created.")
    return layout


# Returns a room after its block and room number have been validated.
def get_room(layout: HostelLayout, block: str, room_no: str) -> Room:
    return layout[block][room_no]


# Prints the occupancy of every room.
def display_occupancy(layout: HostelLayout) -> None:
    print("\n========== HOSTEL OCCUPANCY REPORT ==========")

    for block_name, rooms in layout.items():
        print(f"\n{block_name.upper()}")
        for room_no, room in rooms.items():
            print(f"{room_no}: {room.occupancy_label()}")


# Adds a student's registration number to a room.
def add_occupant(
    layout: HostelLayout,
    block: str,
    room_no: str,
    reg_no: str,
) -> None:
    get_room(layout, block, room_no).occupants.append(reg_no)


# Removes a student's registration number from a room.
def remove_occupant(
    layout: HostelLayout,
    block: str,
    room_no: str,
    reg_no: str,
) -> None:
    room = get_room(layout, block, room_no)
    if reg_no in room.occupants:
        room.occupants.remove(reg_no)


# Calculates the total number of beds.
def total_capacity(layout: HostelLayout) -> int:
    return sum(
        room.capacity
        for rooms in layout.values()
        for room in rooms.values()
    )


# Calculates the total number of occupied beds.
def total_occupied(layout: HostelLayout) -> int:
    return sum(
        len(room.occupants)
        for rooms in layout.values()
        for room in rooms.values()
    )
