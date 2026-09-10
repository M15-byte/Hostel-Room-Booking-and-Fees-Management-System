"""
main.py

Entry point for the Hostel Room Booking System.

Responsible for exactly two things: getting the program into a valid
starting state (either loaded from disk or freshly configured), and then
running the menu loop that routes each choice to the module that
actually knows how to handle it. It never manipulates hostel or student
data directly - that would defeat the point of splitting the system
into separate modules in the first place.

main.py is also the only place that writes to the activity log. Keeping
that decision here, instead of inside hostel.py / students.py / fees.py,
means those modules stay pure business logic - they report success or
failure, and it's main.py's job to decide what's worth recording.
"""

import json

from hostel import (
    build_hostel_layout,
    create_default_layout,
    display_occupancy,
    total_capacity,
    total_occupied,
    HostelLayout,
)
from students import (
    StudentRegistry,
    register_student,
    allocate_room,
    find_by_registration,
    display_student,
)
from fees import record_payment, display_payment_history
from reports import search_student, occupancy_report, fee_defaulters
from file_manager import load_data, save_data, data_file_exists
from activity_log import log_event


MENU_TEXT = """
========================================
     HOSTEL ROOM BOOKING SYSTEM
========================================
1. Register Student 
2. Allocate / Transfer Room
3. Record Fee Payment
4. Search Student
5. View Occupancy Report
6. View Fee Defaulters
7. View Student Details
8. Save Data
9. Exit
10. Set Up Custom Hostel Layout
"""


def ask_float(prompt: str) -> float:
    """Loops until the user enters a number that isn't negative - used
    for both fee totals and payment amounts, which share this exact
    rule even though they mean different things."""
    while True:
        raw_value = input(prompt).strip()
        try:
            value = float(raw_value)
        except ValueError:
            print("Please enter a valid number.")
            continue
        if value < 0:
            print("The amount cannot be negative.")
            continue
        return value


def ask_nonempty(prompt: str) -> str:
    """Re-prompts until something non-blank is entered - used for the
    free-text student details (gender, course, year) so a record can't
    be created with those fields silently left empty."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


def start_up() -> tuple[HostelLayout, StudentRegistry]:
    """
    Gets the program into a usable state before the menu ever appears.

    Three distinct situations are handled on purpose rather than being
    collapsed into one generic 'try to load, otherwise start empty':
    no file yet (first run), a file that loads cleanly, and a file that
    exists but can't be parsed. Each one gets its own message so whoever
    is running the program knows exactly what happened. On a first run -
    or after a damaged file - the predefined default hostel (three
    blocks, 55 beds) is loaded, so the warden never has to answer setup
    questions before the system is usable.
    """
    if not data_file_exists():
        print("No saved data file found - this looks like a first run.")
        print("Loading the predefined default hostel: 3 blocks, 55 beds.")
        return create_default_layout(), {}

    try:
        return load_data()
    except json.JSONDecodeError:
        print("Starting fresh with the default hostel instead, since the")
        print("existing data file can't be used.")
        return create_default_layout(), {}


def handle_register_and_allocate(students: StudentRegistry, layout: HostelLayout) -> None:
    """
    Registers a new student and assigns their room in one continuous
    step, instead of making the warden pick 'Register' and then come
    back to a separate 'Allocate' menu option for every single student.

    If the room step fails (full room, room that doesn't exist), the
    student is still registered - they just aren't given a room yet.
    That's a deliberate choice: refusing the allocation is not a reason
    to throw away the registration details that were already valid.
    """
    print("\n-- Register Student --")
    name = input("Student name: ")
    reg_no = input("Registration number: ")
    gender = ask_nonempty("Gender: ")
    course = ask_nonempty("Course: ")
    year = ask_nonempty("Year of study: ")
    total_fee = ask_float("Total hostel fee for this student: $")

    registered = register_student(students, name, reg_no, gender, course, year, total_fee)
    if not registered:
        return  # register_student() already printed the specific reason

    log_event("registration", f"{name} ({reg_no}) registered with total fee ${total_fee}")

    print("\nNow assign a room for this student.")
    block = input("Block: ")
    room_no = input("Room number: ")

    allocated = allocate_room(students, layout, reg_no, block, room_no)
    if allocated:
        log_event("allocation", f"{name} ({reg_no}) allocated to {block} - Room {room_no}")
    else:
        print("The student is registered but has not been assigned a room.")
        print("Use option 2, 'Allocate / Transfer Room', once a room is available.")


def handle_allocate(students: StudentRegistry, layout: HostelLayout) -> None:
    """Handles room allocation on its own - for a student who was
    registered but couldn't be placed at the time, or for moving an
    already-housed student to a different room."""
    print("\n-- Allocate / Transfer Room --")
    reg_no = input("Registration number: ")
    block = input("Block: ")
    room_no = input("Room number: ")

    allocated = allocate_room(students, layout, reg_no, block, room_no)
    if allocated:
        log_event("allocation", f"{reg_no} allocated to {block} - Room {room_no}")


def handle_payment(students: StudentRegistry) -> None:
    print("\n-- Record Fee Payment --")
    reg_no = input("Registration number: ")
    student = find_by_registration(students, reg_no)
    if student is None:
        print("No student found with that registration number.")
        return
    amount = ask_float("Payment amount: $")

    paid = record_payment(student, amount)
    if paid:
        log_event("payment", f"${amount} paid by {student.name} ({reg_no}); balance now ${student.balance}")


def handle_search(students: StudentRegistry) -> None:
    print("\n-- Search Student --")
    keyword = input("Enter a name or registration number: ")
    results = search_student(students, keyword)
    if not results:
        print("No matching student found.")
        return
    for student in results:
        display_student(student)


def handle_occupancy_report(layout: HostelLayout) -> None:
    """
    Shows the occupancy report, with an optional search built in: press
    Enter to see every block, or type one block name to jump straight
    to it. A block name that doesn't exist gets a clear message instead
    of the screen just doing nothing, which was the actual bug being
    fixed here.
    """
    print("\n-- View Occupancy Report --")
    block_filter = input("Enter a block name to search, or press Enter to view all blocks: ").strip()
    occupancy_report(layout, block_filter)


def handle_defaulters(students: StudentRegistry) -> None:
    print("\n-- Fee Defaulters --")
    threshold = ask_float("Outstanding balance threshold: $")
    fee_defaulters(students, threshold)


def handle_view_student(students: StudentRegistry) -> None:
    """
    Shows full details and payment history for one or more students.

    This now goes through the same search_student() function used by
    option 4, so typing a partial name works here too, not just an
    exact registration number. Previously this only matched an exact
    reg_no and stayed silent on anything else - that silence is what
    looked like the feature "not working."
    """
    print("\n-- View Student Details --")
    keyword = input("Enter a name or registration number: ")
    results = search_student(students, keyword)
    if not results:
        print("No matching student found.")
        return
    for student in results:
        display_student(student)
        display_payment_history(student)


def handle_save(layout: HostelLayout, students: StudentRegistry) -> None:
    save_data(layout, students)
    occupied = total_occupied(layout)
    capacity = total_capacity(layout)
    log_event("save", f"Data saved - {len(students)} student(s) on record, {occupied}/{capacity} beds occupied")


def handle_custom_layout(students: StudentRegistry, layout: HostelLayout) -> None:
    """
    Replaces the predefined default layout with one the user defines.

    Only offered while no students are registered, on purpose: once
    someone has a room, replacing the layout would leave their record
    pointing at a room that no longer exists. When students already
    exist, the option explains this instead of letting the warden break
    the data.
    """
    print("\n-- Set Up Custom Hostel Layout --")
    if students:
        print("This option is only available while no students are registered.")
        print("Replacing the layout now would leave existing room allocations")
        print("pointing at rooms that no longer exist. To start over, delete")
        print("or rename hostel_data.json and run the program again.")
        return

    new_layout = build_hostel_layout()
    layout.clear()
    layout.update(new_layout)
    log_event("setup", f"Custom hostel layout created with {total_capacity(layout)} beds")
    display_occupancy(layout)


# Maps each menu choice to the handler that deals with it. Keeping this
# as data (a dict) rather than a long if/elif chain means adding a tenth
# menu option later is one new entry here, not a new branch buried in a
# growing chain of elifs.
def build_menu_actions(layout: HostelLayout, students: StudentRegistry):
    return {
        "1": lambda: handle_register_and_allocate(students, layout),
        "2": lambda: handle_allocate(students, layout),
        "3": lambda: handle_payment(students),
        "4": lambda: handle_search(students),
        "5": lambda: handle_occupancy_report(layout),
        "6": lambda: handle_defaulters(students),
        "7": lambda: handle_view_student(students),
        "8": lambda: handle_save(layout, students),
        "10": lambda: handle_custom_layout(students, layout),
    }


def main() -> None:
    layout, students = start_up()
    display_occupancy(layout)

    menu_actions = build_menu_actions(layout, students)

    while True:
        print(MENU_TEXT)
        choice = input("Enter your choice: ").strip()

        if choice == "9":
            handle_save(layout, students)
            print("Goodbye!")
            break

        action = menu_actions.get(choice)
        if action is None:
            print("Invalid choice. Please enter a number from 1 to 10.")
            continue

        action()


if __name__ == "__main__":
    main()
