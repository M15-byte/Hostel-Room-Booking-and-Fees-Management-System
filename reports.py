"""
reports.py

Turns the raw student/hostel data into the answers a warden actually
needs on a daily basis: finding one student fast, seeing the whole
building's occupancy at a glance, and listing who still owes money.
"""

from typing import List

from models import Student
from hostel import HostelLayout, resolve_block_name
from students import StudentRegistry, normalize_reg_no


# Searches by registration number first, then by partial name.
def search_student(
    students: StudentRegistry,
    keyword: str,
) -> List[Student]:
    search_text = keyword.strip()
    if not search_text:
        return []

    exact_match = students.get(normalize_reg_no(search_text))
    if exact_match is not None:
        return [exact_match]

    keyword_lower = search_text.casefold()
    return [
        student
        for student in students.values()
        if keyword_lower in student.name.casefold()
    ]


# Prints all blocks or one selected block.
def occupancy_report(
    layout: HostelLayout,
    block_filter: str = "",
) -> None:
    print("\n========== HOSTEL OCCUPANCY REPORT ==========")

    if block_filter.strip():
        canonical_block = resolve_block_name(layout, block_filter)
        if canonical_block is None:
            print(f"\nNo block named '{block_filter.strip()}' was found.")
            print(f"Available blocks: {', '.join(layout.keys())}")
            return
        blocks_to_show = {canonical_block: layout[canonical_block]}
    else:
        blocks_to_show = layout

    for block_name, rooms in blocks_to_show.items():
        print(f"\n{block_name.upper()}")
        for room_no, room in rooms.items():
            print(f"{room_no}: {room.occupancy_label()}")


# Lists students whose balance is above the given threshold.
def fee_defaulters(
    students: StudentRegistry,
    threshold: float,
) -> None:
    print("\n========== FEE DEFAULTERS ==========\n")

    defaulters = [
        student
        for student in students.values()
        if student.balance > threshold
    ]
    defaulters.sort(key=lambda student: student.balance, reverse=True)

    if not defaulters:
        print("No students above this threshold.")
        return

    for student in defaulters:
        print(
            f"{student.name:<20} {student.reg_no:<15} "
            f"Outstanding: ${student.balance:.2f}"
        )
