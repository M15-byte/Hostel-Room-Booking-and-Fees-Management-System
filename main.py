"""
main.py

Entry point for the Hostel Room Booking System.

Responsible for getting the program into a valid
starting state (either loaded from disk or freshly configured), and then
running the menu loop that routes each choice to the module that
actually knows how to handle it. 
main.py also writes to the activity log. Keeping
that decision here, instead of inside hostel.py / students.py / fees.py,
means those modules stay pure business logic - they report success or
failure, and it's main.py's job to decide what's worth recording.
"""

import math

from activity_log import log_event
from fees import display_payment_history, record_payment
from file_manager import (
    DATA_FILE,
    DataFileError,
    data_file_exists,
    load_data,
    save_data,
)
from hostel import (
    HostelLayout,
    build_hostel_layout,
    create_default_layout,
    display_occupancy,
    total_capacity,
    total_occupied,
)
from reports import fee_defaulters, occupancy_report, search_student
from students import (
    StudentRegistry,
    allocate_room,
    display_student,
    find_by_registration,
    register_student,
)


# Menu displayed after each operation.
MENU_TEXT = """
========================================
     HOSTEL ROOM BOOKING SYSTEM
========================================
1. Register Student (includes Room Allocation)
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


# Repeats a prompt until a valid money amount is entered.
def ask_amount(prompt: str, allow_zero: bool = False) -> float:
    while True:
        raw_value = input(prompt).strip()

        try:
            value = float(raw_value)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if not math.isfinite(value):
            print("Please enter a valid number.")
            continue
        if value < 0:
            print("The amount cannot be negative.")
            continue
        if value == 0 and not allow_zero:
            print("The amount must be greater than zero.")
            continue

        return round(value, 2)


# Repeats a prompt until text is entered.
def ask_nonempty(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("This field cannot be empty.")


# Repeats a prompt until y or n is entered.
def ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt).strip().casefold()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter y or n.")


# Loads saved data or creates the default hostel.
def start_up() -> tuple[HostelLayout, StudentRegistry]:
    if not data_file_exists():
        print("No saved data file found - this looks like a first run.")
        print("Loading the predefined default hostel: 3 blocks, 55 beds.")
        return create_default_layout(), {}

    try:
        return load_data()
    except FileNotFoundError:
        print("The saved data file disappeared before it could be opened.")
    except DataFileError as error:
        print(f"Warning: the saved data file is damaged: {error}")

    print("Starting with the predefined default hostel instead.")
    return create_default_layout(), {}


# Registers a student and asks for the first room allocation.
def handle_register_and_allocate(
    students: StudentRegistry,
    layout: HostelLayout,
) -> None:
    print("\n-- Register Student --")
    name = ask_nonempty("Student name: ")
    reg_no = ask_nonempty("Registration number: ")
    gender = ask_nonempty("Gender: ")
    course = ask_nonempty("Course: ")
    year = ask_nonempty("Year of study: ")
    total_fee = ask_amount("Total hostel fee for this student: $")

    registered = register_student(
        students,
        name,
        reg_no,
        gender,
        course,
        year,
        total_fee,
    )
    if not registered:
        return

    student = find_by_registration(students, reg_no)
    if student is None:
        return

    log_event(
        "registration",
        f"{student.name} ({student.reg_no}) registered with fee ${student.total_fee:.2f}",
    )

    print("\nNow assign a room for this student.")
    block = ask_nonempty("Block (e.g. A or Block A): ")
    room_no = ask_nonempty("Room number (e.g. 1, 01 or A01): ")

    if allocate_room(students, layout, student.reg_no, block, room_no):
        log_event(
            "allocation",
            f"{student.name} ({student.reg_no}) allocated to "
            f"{student.block} - Room {student.room}",
        )
    else:
        print("The student is registered but has not been assigned a room.")
        print("Use option 2 to allocate a room later.")


# Allocates or transfers an existing student.
def handle_allocate(
    students: StudentRegistry,
    layout: HostelLayout,
) -> None:
    print("\n-- Allocate / Transfer Room --")
    reg_no = ask_nonempty("Registration number: ")
    block = ask_nonempty("Block (e.g. A or Block A): ")
    room_no = ask_nonempty("Room number (e.g. 1, 01 or A01): ")

    if allocate_room(students, layout, reg_no, block, room_no):
        student = find_by_registration(students, reg_no)
        if student is None:
            return

        log_event(
            "allocation",
            f"{student.reg_no} allocated to {student.block} - Room {student.room}",
        )


# Records a fee payment for one student.
def handle_payment(students: StudentRegistry) -> None:
    print("\n-- Record Fee Payment --")
    reg_no = ask_nonempty("Registration number: ")
    student = find_by_registration(students, reg_no)

    if student is None:
        print("No student found with that registration number.")
        return

    amount = ask_amount("Payment amount: $")
    if record_payment(student, amount):
        log_event(
            "payment",
            f"${amount:.2f} paid by {student.name} ({student.reg_no}); "
            f"balance ${student.balance:.2f}",
        )


# Searches for students by name or registration number.
def handle_search(students: StudentRegistry) -> None:
    print("\n-- Search Student --")
    keyword = ask_nonempty("Enter a name or registration number: ")
    results = search_student(students, keyword)

    if not results:
        print("No matching student found.")
        return

    for student in results:
        display_student(student)


# Displays all blocks or one selected block.
def handle_occupancy_report(layout: HostelLayout) -> None:
    print("\n-- View Occupancy Report --")
    block_filter = input(
        "Enter a block name, or press Enter to view all blocks: "
    ).strip()
    occupancy_report(layout, block_filter)


# Displays students whose balances are above a threshold.
def handle_defaulters(students: StudentRegistry) -> None:
    print("\n-- Fee Defaulters --")
    threshold = ask_amount(
        "Outstanding balance threshold: $",
        allow_zero=True,
    )
    fee_defaulters(students, threshold)


# Displays full details and payment history for matching students.
def handle_view_student(students: StudentRegistry) -> None:
    print("\n-- View Student Details --")
    keyword = ask_nonempty("Enter a name or registration number: ")
    results = search_student(students, keyword)

    if not results:
        print("No matching student found.")
        return

    for student in results:
        display_student(student)
        display_payment_history(student)


# Saves data and writes a save event to the activity log.
def handle_save(
    layout: HostelLayout,
    students: StudentRegistry,
) -> bool:
    if not save_data(layout, students):
        return False

    log_event(
        "save",
        f"{len(students)} student(s), "
        f"{total_occupied(layout)}/{total_capacity(layout)} beds occupied",
    )
    return True


# Replaces the default layout before students are registered.
def handle_custom_layout(
    students: StudentRegistry,
    layout: HostelLayout,
) -> None:
    print("\n-- Set Up Custom Hostel Layout --")

    if students:
        print("This option is only available when no students are registered.")
        print(f"To start again, remove or rename: {DATA_FILE.name}")
        return

    new_layout = build_hostel_layout()
    layout.clear()
    layout.update(new_layout)
    log_event(
        "setup",
        f"Custom layout created with {total_capacity(layout)} beds",
    )
    display_occupancy(layout)


# Runs the validated menu until the user exits.
def main() -> None:
    layout, students = start_up()
    display_occupancy(layout)

    while True:
        print(MENU_TEXT)
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            handle_register_and_allocate(students, layout)
        elif choice == "2":
            handle_allocate(students, layout)
        elif choice == "3":
            handle_payment(students)
        elif choice == "4":
            handle_search(students)
        elif choice == "5":
            handle_occupancy_report(layout)
        elif choice == "6":
            handle_defaulters(students)
        elif choice == "7":
            handle_view_student(students)
        elif choice == "8":
            handle_save(layout, students)
        elif choice == "9":
            if handle_save(layout, students):
                print("Goodbye!")
                break
            if ask_yes_no("Exit without saving? (y/n): "):
                print("Goodbye!")
                break
        elif choice == "10":
            handle_custom_layout(students, layout)
        else:
            print("Invalid choice. Please enter a number from 1 to 10.")


# Starts the program when this file is run directly.
if __name__ == "__main__":
    main()
