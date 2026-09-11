
"""
Handles saving and loading program data using JSON.
This module converts dataclasses into dictionaries for storage
and rebuilds them when data is loaded.
"""

import json
import math
from dataclasses import asdict
from pathlib import Path
from typing import Tuple

from models import Payment, Room, Student
from hostel import HostelLayout, room_exists, resolve_block_name, resolve_room_number
from students import StudentRegistry, normalize_reg_no


# The data file is kept in the same folder as the program.
DATA_FILE = Path(__file__).resolve().parent / "hostel_data.json"


# Raised when a saved file exists but contains invalid data.
class DataFileError(Exception):
    pass


# Converts room objects to dictionaries for JSON.
def _layout_to_dict(layout: HostelLayout) -> dict:
    result = {}

    for block, rooms in layout.items():
        result[block] = {}
        for room_no, room in rooms.items():
            room_data = asdict(room)
            room_data["occupied"] = len(room.occupants) > 0
            room_data["status"] = "FULL" if room.is_full() else "AVAILABLE"
            result[block][room_no] = room_data

    return result


# Rebuilds room objects from saved JSON data.
def _layout_from_dict(raw: dict) -> HostelLayout:
    if not isinstance(raw, dict) or not raw:
        raise ValueError("The hostel layout is missing or empty.")

    layout: HostelLayout = {}

    for block, rooms in raw.items():
        if not isinstance(block, str) or not block.strip():
            raise ValueError("A block name is invalid.")
        if not isinstance(rooms, dict) or not rooms:
            raise ValueError(f"{block} has no valid rooms.")

        layout[block] = {}
        for room_no, room_data in rooms.items():
            if not isinstance(room_no, str) or not room_no.strip():
                raise ValueError(f"A room number in {block} is invalid.")
            if not isinstance(room_data, dict):
                raise ValueError(f"Room {room_no} has invalid data.")

            capacity = room_data.get("capacity")
            occupants = room_data.get("occupants", [])

            if isinstance(capacity, bool) or not isinstance(capacity, int):
                raise ValueError(f"Room {room_no} has an invalid capacity.")
            if capacity <= 0:
                raise ValueError(f"Room {room_no} has an invalid capacity.")
            if not isinstance(occupants, list):
                raise ValueError(f"Room {room_no} has an invalid occupant list.")

            clean_occupants = []
            for reg_no in occupants:
                if not isinstance(reg_no, str) or not normalize_reg_no(reg_no):
                    raise ValueError(f"Room {room_no} has an invalid occupant.")
                clean_occupants.append(normalize_reg_no(reg_no))

            if len(clean_occupants) != len(set(clean_occupants)):
                raise ValueError(f"Room {room_no} contains a duplicate occupant.")

            layout[block][room_no] = Room(
                capacity=capacity,
                occupants=clean_occupants,
            )

    return layout


# Converts student objects to dictionaries for JSON.
def _students_to_dict(students: StudentRegistry) -> dict:
    return {
        reg_no: asdict(student)
        for reg_no, student in students.items()
    }


# Checks and rebuilds one saved payment.
def _payment_from_dict(raw: dict) -> Payment:
    if not isinstance(raw, dict):
        raise ValueError("A payment record is invalid.")

    amount = raw.get("amount")
    payment_date = raw.get("date")

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ValueError("A payment amount is invalid.")
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError("A payment amount is invalid.")
    if not isinstance(payment_date, str) or not payment_date.strip():
        raise ValueError("A payment date is invalid.")

    return Payment(amount=round(float(amount), 2), date=payment_date)


# Rebuilds student objects from saved JSON data.
def _students_from_dict(raw: dict) -> StudentRegistry:
    if not isinstance(raw, dict):
        raise ValueError("The student records are invalid.")

    students: StudentRegistry = {}

    for saved_key, data in raw.items():
        if not isinstance(saved_key, str) or not isinstance(data, dict):
            raise ValueError("A student record is invalid.")

        name = data.get("name")
        reg_no = data.get("reg_no")
        gender = data.get("gender")
        course = data.get("course")
        year = data.get("year")
        total_fee = data.get("total_fee")
        amount_paid = data.get("amount_paid", 0.0)
        block = data.get("block", "")
        room = data.get("room", "")
        payment_data = data.get("payments", [])

        text_fields = (name, reg_no, gender, course, year, block, room)
        if not all(isinstance(value, str) for value in text_fields):
            raise ValueError("A student text field is invalid.")
        if not all(value.strip() for value in (name, reg_no, gender, course, year)):
            raise ValueError("A required student field is empty.")

        clean_reg_no = normalize_reg_no(reg_no)
        if clean_reg_no != normalize_reg_no(saved_key):
            raise ValueError("A student registration number does not match its key.")
        if clean_reg_no in students:
            raise ValueError("A registration number is duplicated.")

        numbers = (total_fee, amount_paid)
        if any(isinstance(value, bool) for value in numbers):
            raise ValueError("A student fee value is invalid.")
        if not all(isinstance(value, (int, float)) for value in numbers):
            raise ValueError("A student fee value is invalid.")
        if not all(math.isfinite(value) for value in numbers):
            raise ValueError("A student fee value is invalid.")
        if total_fee <= 0 or amount_paid < 0 or amount_paid > total_fee:
            raise ValueError("A student fee value is outside the valid range.")
        if not isinstance(payment_data, list):
            raise ValueError("A student's payment history is invalid.")

        payments = [_payment_from_dict(item) for item in payment_data]
        payment_total = round(sum(item.amount for item in payments), 2)
        if payment_total != round(float(amount_paid), 2):
            raise ValueError("A student's payment total does not match the history.")

        students[clean_reg_no] = Student(
            name=name.strip(),
            reg_no=clean_reg_no,
            gender=gender.strip(),
            course=course.strip(),
            year=year.strip(),
            total_fee=round(float(total_fee), 2),
            block=block.strip(),
            room=room.strip(),
            amount_paid=round(float(amount_paid), 2),
            payments=payments,
        )

    return students


# Confirms that students and room occupants agree after loading.
def _validate_loaded_data(
    layout: HostelLayout,
    students: StudentRegistry,
) -> None:
    seen_occupants = set()

    for block, rooms in layout.items():
        for room_no, room in rooms.items():
            if len(room.occupants) > room.capacity:
                raise ValueError(f"Room {room_no} is over capacity.")

            for reg_no in room.occupants:
                if reg_no in seen_occupants:
                    raise ValueError(f"Student {reg_no} appears in two rooms.")
                if reg_no not in students:
                    raise ValueError(f"Room {room_no} contains an unknown student.")

                student = students[reg_no]
                if student.block != block or student.room != room_no:
                    raise ValueError(f"Room details for {reg_no} do not match.")
                seen_occupants.add(reg_no)

    for reg_no, student in students.items():
        if bool(student.block) != bool(student.room):
            raise ValueError(f"Student {reg_no} has incomplete room details.")

        if student.is_allocated:
            canonical_block = resolve_block_name(layout, student.block)
            if canonical_block is None:
                raise ValueError(f"Student {reg_no} has an unknown block.")

            canonical_room = resolve_room_number(
                layout,
                canonical_block,
                student.room,
            )
            if canonical_room is None:
                raise ValueError(f"Student {reg_no} has an unknown room.")

            student.block = canonical_block
            student.room = canonical_room

            if not room_exists(layout, canonical_block, canonical_room):
                raise ValueError(f"Student {reg_no} has an unknown room.")
            if reg_no not in layout[canonical_block][canonical_room].occupants:
                raise ValueError(f"Student {reg_no} is missing from the room list.")
        elif reg_no in seen_occupants:
            raise ValueError(f"Student {reg_no} has conflicting room details.")


# Checks whether saved data is available.
def data_file_exists() -> bool:
    return DATA_FILE.exists()


# Loads and validates the saved hostel data.
def load_data() -> Tuple[HostelLayout, StudentRegistry]:
    print("Loading saved data...")

    try:
        with DATA_FILE.open("r", encoding="utf-8") as file:
            raw = json.load(file)
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DataFileError(str(error)) from error

    try:
        if not isinstance(raw, dict):
            raise ValueError("The main JSON value must be an object.")

        layout = _layout_from_dict(raw["hostel_layout"])
        students = _students_from_dict(raw["students"])
        _validate_loaded_data(layout, students)
    except (KeyError, TypeError, ValueError) as error:
        raise DataFileError(str(error)) from error

    print("Data loaded successfully.")
    return layout, students


# Saves all current data and returns True when successful.
def save_data(
    layout: HostelLayout,
    students: StudentRegistry,
) -> bool:
    print("\nSaving data...")

    payload = {
        "hostel_layout": _layout_to_dict(layout),
        "students": _students_to_dict(students),
    }
    temporary_file = DATA_FILE.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=4, allow_nan=False)
        temporary_file.replace(DATA_FILE)
    except (OSError, TypeError, ValueError) as error:
        print(f"Data could not be saved: {error}")
        try:
            temporary_file.unlink(missing_ok=True)
        except OSError:
            pass
        return False

    print("Data saved successfully.")
    return True
