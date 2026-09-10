"""
students.py

Registration, validation and room allocation for individual students.

Students are kept in a dictionary keyed by registration number rather
than a list, so looking one up is a direct dictionary access instead of
a linear scan - the difference only matters at scale, but it costs
nothing to get right from the start.
"""

from typing import Dict, List, Optional
from models import Student
from hostel import HostelLayout, room_exists, get_room, add_occupant, remove_occupant

StudentRegistry = Dict[str, Student]


def registration_number_taken(students: StudentRegistry, reg_no: str) -> bool:
    return reg_no in students


def validate_new_student(name: str, reg_no: str, students: StudentRegistry) -> Optional[str]:
    """
    Runs every check a new registration has to pass.

    Returns None when the details are valid, or a human-readable reason
    when they are not. Returning the reason (instead of just True/False)
    means the caller can show the user exactly what went wrong without
    this function needing to know anything about print statements.
    """
    if not name.strip():
        return "Student name cannot be empty."
    if not reg_no.strip():
        return "Registration number cannot be empty."
    if registration_number_taken(students, reg_no):
        return f"Registration number '{reg_no}' is already in use."
    return None


def register_student(
    students: StudentRegistry,
    name: str,
    reg_no: str,
    gender: str,
    course: str,
    year: str,
    total_fee: float,
) -> bool:
    """
    Validates and creates a new Student record.

    total_fee is passed in rather than assumed, because two students in
    this same hostel might legitimately owe different amounts - a returning
    student on a scholarship and a new student paying in full shouldn't be
    forced to share one hardcoded number.
    """
    error = validate_new_student(name, reg_no, students)
    if error:
        print(f"Registration failed. {error}")
        return False

    students[reg_no] = Student(
        name=name.strip(),
        reg_no=reg_no.strip(),
        gender=gender.strip(),
        course=course.strip(),
        year=year.strip(),
        total_fee=total_fee,
    )
    print(f"Student registered successfully.\n{name} ({reg_no}) added to the system.")
    return True


def allocate_room(
    students: StudentRegistry,
    layout: HostelLayout,
    reg_no: str,
    block: str,
    room_no: str,
) -> bool:
    """
    Moves a student into a room, provided the student and room both exist
    and the room has space.

    If the student already has a room, they're removed from it first -
    this doubles as the "transfer a student to a different room" path,
    since a fresh allocation and a transfer are really the same operation.
    """
    student = students.get(reg_no)
    if student is None:
        print(f"Allocation failed. No student found with registration number {reg_no}.")
        return False

    if not room_exists(layout, block, room_no):
        print(f"Allocation failed. Room {room_no} does not exist in {block}.")
        return False

    room = get_room(layout, block, room_no)
    if not room.has_space():
        print("Allocation failed.")
        print(f"Room {room_no} is already full.")
        print(f"Capacity: {room.capacity}")
        print(f"Current occupancy: {len(room.occupants)}")
        return False

    if student.is_allocated:
        remove_occupant(layout, student.block, student.room, reg_no)

    add_occupant(layout, block, room_no, reg_no)
    student.block = block
    student.room = room_no

    print(f"{student.name} allocated to {block} - Room {room_no}.")
    print(f"Room {room_no} now has {len(room.occupants)}/{room.capacity} occupants.")
    return True


def find_by_registration(students: StudentRegistry, reg_no: str) -> Optional[Student]:
    return students.get(reg_no)


def find_by_name(students: StudentRegistry, keyword: str) -> List[Student]:
    keyword_lower = keyword.strip().lower()
    return [s for s in students.values() if keyword_lower in s.name.lower()]


def display_student(student: Student) -> None:
    print("\nStudent found:")
    print(f"Name: {student.name}")
    print(f"Reg No: {student.reg_no}")
    print(f"Course: {student.course}")
    print(f"Block: {student.block or '-'}")
    print(f"Room: {student.room or '-'}")
    print(f"Fees Paid: ${student.amount_paid}")
    print(f"Outstanding: ${student.balance}")
