"""
file_manager.py

Reads and writes the program's data to a JSON file on disk.

JSON has no idea what a Room or a Student dataclass is, so this module's
whole job is translating between "dataclasses in memory" and "plain
dictionaries JSON can store" in both directions, and doing it in exactly
one place so the rest of the codebase never has to think about it.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Tuple

from models import Room, Student, Payment
from hostel import HostelLayout
from students import StudentRegistry

DATA_FILE = Path("hostel_data.json")


def _layout_to_dict(layout: HostelLayout) -> dict:
    """
    Converts every Room object in the layout into a plain dict.

    Two read-only fields are added here purely for whoever opens
    hostel_data.json directly - neither is something the Room dataclass
    stores; both are worked out fresh from occupants/capacity every time
    this function runs, so the file always reflects the true state at
    the moment it was saved:

    - "occupied": true the instant a room has even one student in it.
      This is the field to check if you just assigned someone a room
      and want to confirm it took effect - a room can be occupied long
      before it's full.
    - "status": "FULL" only once occupants reaches capacity, "AVAILABLE"
      otherwise. This is about whether the room can still take another
      student, which is a different question from "occupied".
    """
    result: dict = {}
    for block, rooms in layout.items():
        result[block] = {}
        for room_no, room in rooms.items():
            room_dict = asdict(room)
            room_dict["occupied"] = len(room.occupants) > 0
            room_dict["status"] = "FULL" if room.is_full() else "AVAILABLE"
            result[block][room_no] = room_dict
    return result


def _layout_from_dict(raw: dict) -> HostelLayout:
    """
    Rebuilds Room objects from the plain dicts stored in the JSON file.

    "occupied" and "status" are dropped before the Room is rebuilt,
    since neither is one of the dataclass's real fields - passing them
    straight into Room(**room_data) would raise a TypeError. Filtering
    to the fields the dataclass actually accepts also means older data
    files saved before these existed still load without a special case.
    """
    layout: HostelLayout = {}
    for block, rooms in raw.items():
        layout[block] = {}
        for room_no, room_data in rooms.items():
            known_fields = {"capacity": room_data["capacity"], "occupants": room_data.get("occupants", [])}
            layout[block][room_no] = Room(**known_fields)
    return layout


def _students_to_dict(students: StudentRegistry) -> dict:
    """
    asdict() walks nested dataclasses automatically, so a Student's list
    of Payment objects is already converted to a list of plain dicts by
    the time this returns - there's no need to loop over payments by hand.
    """
    return {reg_no: asdict(student) for reg_no, student in students.items()}


def _students_from_dict(raw: dict) -> StudentRegistry:
    """
    The reverse of _students_to_dict(). Payment objects have to be
    rebuilt explicitly here, because asdict() flattens them to dicts on
    the way out, but nothing on the way in automatically turns a dict
    back into a Payment - that direction has to be done by hand.
    """
    students: StudentRegistry = {}
    for reg_no, data in raw.items():
        payment_dicts = data.pop("payments", [])
        payments = [Payment(**p) for p in payment_dicts]
        students[reg_no] = Student(payments=payments, **data)
    return students


def data_file_exists() -> bool:
    return DATA_FILE.exists()


def load_data() -> Tuple[HostelLayout, StudentRegistry]:
    """
    Loads the hostel layout and student registry from disk.

    A missing file and a corrupted file are handled as two distinct,
    named cases rather than one broad except-and-hope: the caller (and
    anyone reading the logs later) can tell "there's nothing here yet"
    apart from "something here is broken."
    """
    print("Loading saved data...")
    try:
        with DATA_FILE.open("r") as file:
            raw = json.load(file)
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as error:
        print("Warning: the saved data file exists but could not be read.")
        print(f"Details: {error}")
        raise

    layout = _layout_from_dict(raw["hostel_layout"])
    students = _students_from_dict(raw["students"])
    print("Data loaded successfully.")
    return layout, students


def save_data(layout: HostelLayout, students: StudentRegistry) -> None:
    print("\nSaving data...")
    payload = {
        "hostel_layout": _layout_to_dict(layout),
        "students": _students_to_dict(students),
    }
    with DATA_FILE.open("w") as file:
        json.dump(payload, file, indent=4)
    print("Data saved successfully.")
