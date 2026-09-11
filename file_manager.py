
"""
Handles saving and loading program data using JSON.
This module converts dataclasses into dictionaries for storage
and rebuilds them when data is loaded.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import Tuple
from models import Room, Student, Payment
from hostel import HostelLayout
from students import StudentRegistry

DATA_FILE = Path("hostel_data.json")


# Convert the hostel layout into JSON-friendly dictionaries
def _layout_to_dict(layout: HostelLayout) -> dict:
    result: dict = {}

    for block, rooms in layout.items():
        result[block] = {}

        for room_no, room in rooms.items():
            room_dict = asdict(room)

            # Add calculated room information for the saved file
            room_dict["occupied"] = len(room.occupants) > 0
            room_dict["status"] = "FULL" if room.is_full() else "AVAILABLE"

            result[block][room_no] = room_dict

    return result


# Rebuild Room objects from saved dictionaries
def _layout_from_dict(raw: dict) -> HostelLayout:
    layout: HostelLayout = {}

    for block, rooms in raw.items():
        layout[block] = {}

        for room_no, room_data in rooms.items():
            # Keep only fields needed to create a Room
            known_fields = {
                "capacity": room_data["capacity"],
                "occupants": room_data.get("occupants", [])
            }

            layout[block][room_no] = Room(**known_fields)

    return layout


# Convert all Student objects into dictionaries
def _students_to_dict(students: StudentRegistry) -> dict:
    return {reg_no: asdict(student) for reg_no, student in students.items()}


# Rebuild Student and Payment objects from saved data
def _students_from_dict(raw: dict) -> StudentRegistry:
    students: StudentRegistry = {}

    for reg_no, data in raw.items():
        # Rebuild each payment as a Payment object
        payment_dicts = data.pop("payments", [])
        payments = [Payment(**p) for p in payment_dicts]

        students[reg_no] = Student(payments=payments, **data)

    return students


# Check whether saved data exists
def data_file_exists() -> bool:
    return DATA_FILE.exists()


# Load saved hostel and student data
def load_data() -> Tuple[HostelLayout, StudentRegistry]:
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

    # Convert saved dictionaries back into objects
    layout = _layout_from_dict(raw["hostel_layout"])
    students = _students_from_dict(raw["students"])

    print("Data loaded successfully.")
    return layout, students


# Save the current hostel and student data
def save_data(layout: HostelLayout, students: StudentRegistry) -> None:
    print("\nSaving data...")

    # Prepare all data for JSON storage
    payload = {
        "hostel_layout": _layout_to_dict(layout),
        "students": _students_to_dict(students),
    }

    with DATA_FILE.open("w") as file:
        json.dump(payload, file, indent=4)

    print("Data saved successfully.")
