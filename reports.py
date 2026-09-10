"""
reports.py

Turns the raw student/hostel data into the answers a warden actually
needs on a daily basis: finding one student fast, seeing the whole
building's occupancy at a glance, and listing who still owes money.
"""

from typing import List
from models import Student
from students import StudentRegistry
from hostel import HostelLayout


def search_student(students: StudentRegistry, keyword: str) -> List[Student]:
    """
    Tries an exact registration-number match first, since that's the
    fastest and most precise lookup available (a direct dict access).
    Only falls back to a partial name search if that lookup misses,
    so a search for a reg number that also happens to look like a name
    substring still resolves to the exact student.
    """
    exact_match = students.get(keyword)
    if exact_match is not None:
        return [exact_match]

    keyword_lower = keyword.strip().lower()
    return [s for s in students.values() if keyword_lower in s.name.lower()]


def occupancy_report(layout: HostelLayout, block_filter: str = "") -> None:
    """
    Prints the occupancy report, optionally narrowed to one block.

    block_filter being empty shows everything, same as before. A
    non-empty filter that doesn't match any real block name prints a
    clear message and returns - it does not fail silently, and it does
    not fall back to showing the full report, which would be confusing
    after someone deliberately asked to search for one block.
    """
    print("\n========== HOSTEL OCCUPANCY REPORT ==========")

    if block_filter:
        if block_filter not in layout:
            print(f"\nNo block named '{block_filter}' was found.")
            return
        blocks_to_show = {block_filter: layout[block_filter]}
    else:
        blocks_to_show = layout

    for block_name, rooms in blocks_to_show.items():
        print(f"\n{block_name.upper()}")
        for room_no, room in rooms.items():
            print(f"{room_no}: {room.occupancy_label()}")


def fee_defaulters(students: StudentRegistry, threshold: float) -> None:
    """Lists every student whose outstanding balance meets or exceeds
    the given threshold, sorted highest balance first so the biggest
    outstanding amounts are the first thing the warden sees."""
    print("\n========== FEE DEFAULTERS ==========\n")

    defaulters = [s for s in students.values() if s.balance >= threshold]
    defaulters.sort(key=lambda s: s.balance, reverse=True)

    if not defaulters:
        print("No students at or above this threshold.")
        return

    for student in defaulters:
        print(f"{student.name:<15} {student.reg_no:<12} Outstanding: ${student.balance}")
