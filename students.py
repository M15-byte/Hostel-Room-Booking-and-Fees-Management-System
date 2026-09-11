"""
students.py

Registration, validation and room allocation for individual students.

Students are kept in a dictionary keyed by registration number rather
than a list, so looking one up is a direct dictionary access instead of
a linear scan - the difference only matters at scale, but it costs
nothing to get right from the start.
"""

import math
from typing import Dict, List, Optional

from models import Student
from hostel import (
    HostelLayout,
    resolve_block_name,
    resolve_room_number,
    get_room,
    add_occupant,
    remove_occupant,
)


# Students are stored using their registration number as the key.
StudentRegistry = Dict[str, Student]


# Removes surrounding spaces and uses uppercase for registration numbers.
def normalize_reg_no(reg_no: str) -> str:
    return reg_no.strip().upper()


# Checks whether a registration number is already stored.
def registration_number_taken(
    students: StudentRegistry,
    reg_no: str,
) -> bool:
    return normalize_reg_no(reg_no) in students


# Validates the details needed to register a student.
def validate_new_student(
    name: str,
    reg_no: str,
    gender: str,
    course: str,
    year: str,
    total_fee: float,
    students: StudentRegistry,
) -> Optional[str]:
    if not name.strip():
        return "Student name cannot be empty."
    if not normalize_reg_no(reg_no):
        return "Registration number cannot be empty."
    if not gender.strip():
        return "Gender cannot be empty."
    if not course.strip():
        return "Course cannot be empty."
    if not year.strip():
        return "Year of study cannot be empty."
    if not math.isfinite(total_fee) or total_fee <= 0:
        return "Total hostel fee must be greater than zero."
    if registration_number_taken(students, reg_no):
        return f"Registration number '{normalize_reg_no(reg_no)}' is already in use."
    return None


# Creates and stores a new student record.
def register_student(
    students: StudentRegistry,
    name: str,
    reg_no: str,
    gender: str,
    course: str,
    year: str,
    total_fee: float,
) -> bool:
    error = validate_new_student(
        name,
        reg_no,
        gender,
        course,
        year,
        total_fee,
        students,
    )
    if error:
        print(f"Registration failed. {error}")
        return False

    clean_reg_no = normalize_reg_no(reg_no)
    student = Student(
        name=name.strip(),
        reg_no=clean_reg_no,
        gender=gender.strip(),
        course=course.strip(),
        year=year.strip(),
        total_fee=round(total_fee, 2),
    )
    students[clean_reg_no] = student

    print("Student registered successfully.")
    print(f"{student.name} ({student.reg_no}) added to the system.")
    return True


# Allocates a room or transfers a student to another room.
def allocate_room(
    students: StudentRegistry,
    layout: HostelLayout,
    reg_no: str,
    block: str,
    room_no: str,
) -> bool:
    clean_reg_no = normalize_reg_no(reg_no)
    student = students.get(clean_reg_no)

    if student is None:
        print(
            "Allocation failed. No student found with registration "
            f"number {clean_reg_no}."
        )
        return False

    canonical_block = resolve_block_name(layout, block)
    if canonical_block is None:
        print(f"Allocation failed. Block '{block.strip()}' does not exist.")
        print(f"Available blocks: {', '.join(layout.keys())}")
        return False

    canonical_room = resolve_room_number(layout, canonical_block, room_no)
    if canonical_room is None:
        print(
            f"Allocation failed. Room '{room_no.strip()}' does not exist "
            f"in {canonical_block}."
        )
        print(f"Available rooms: {', '.join(layout[canonical_block].keys())}")
        return False

    if student.block == canonical_block and student.room == canonical_room:
        print(
            f"{student.name} is already allocated to "
            f"{canonical_block} - Room {canonical_room}."
        )
        return True

    room = get_room(layout, canonical_block, canonical_room)
    if not room.has_space():
        print("Allocation failed.")
        print(f"Room {canonical_room} is already full.")
        print(f"Capacity: {room.capacity}")
        print(f"Current occupancy: {len(room.occupants)}")
        return False

    if student.is_allocated:
        remove_occupant(
            layout,
            student.block,
            student.room,
            clean_reg_no,
        )

    add_occupant(
        layout,
        canonical_block,
        canonical_room,
        clean_reg_no,
    )
    student.block = canonical_block
    student.room = canonical_room

    print(
        f"{student.name} allocated to "
        f"{canonical_block} - Room {canonical_room}."
    )
    print(
        f"Room {canonical_room} now has "
        f"{len(room.occupants)}/{room.capacity} occupants."
    )
    return True


# Finds one student using a registration number.
def find_by_registration(
    students: StudentRegistry,
    reg_no: str,
) -> Optional[Student]:
    return students.get(normalize_reg_no(reg_no))


# Finds students whose names contain the search text.
def find_by_name(
    students: StudentRegistry,
    keyword: str,
) -> List[Student]:
    keyword_lower = keyword.strip().casefold()
    if not keyword_lower:
        return []
    return [
        student
        for student in students.values()
        if keyword_lower in student.name.casefold()
    ]


# Prints a student's hostel and fee details.
def display_student(student: Student) -> None:
    print("\nStudent found:")
    print(f"Name: {student.name}")
    print(f"Reg No: {student.reg_no}")
    print(f"Gender: {student.gender}")
    print(f"Course: {student.course}")
    print(f"Year of Study: {student.year}")
    print(f"Block: {student.block or '-'}")
    print(f"Room: {student.room or '-'}")
    print(f"Total Fee: ${student.total_fee:.2f}")
    print(f"Fees Paid: ${student.amount_paid:.2f}")
    print(f"Outstanding: ${student.balance:.2f}")

