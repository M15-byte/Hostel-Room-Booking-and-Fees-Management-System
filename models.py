"""
models.py

Defines the data structures shared across the whole application.

Using dataclasses here instead of raw dictionaries gives us three things
a plain dict can't: type hints that an IDE/linter can check, a single
place to see every field a Room/Student/Payment actually has, and
computed properties (like Student.balance) that can never drift out of
sync with the underlying numbers, because they're calculated on read
instead of being stored separately.
"""

from dataclasses import dataclass, field
from typing import List


# Stores one fee payment.
@dataclass
class Payment:
    amount: float
    date: str


# Stores a room and its occupants.
@dataclass
class Room:
    capacity: int
    occupants: List[str] = field(default_factory=list)

    # Returns True when all beds are occupied.
    def is_full(self) -> bool:
        return len(self.occupants) >= self.capacity

    # Returns True when the room has a free bed.
    def has_space(self) -> bool:
        return not self.is_full()

    # Returns the room occupancy in a readable format.
    def occupancy_label(self) -> str:
        status = "FULL" if self.is_full() else "AVAILABLE"
        return f"{len(self.occupants)}/{self.capacity} - {status}"


# Stores a student's hostel and fee details.
@dataclass
class Student:
    name: str
    reg_no: str
    gender: str
    course: str
    year: str
    total_fee: float
    block: str = ""
    room: str = ""
    amount_paid: float = 0.0
    payments: List[Payment] = field(default_factory=list)

    # Calculates the current outstanding balance.
    @property
    def balance(self) -> float:
        return round(self.total_fee - self.amount_paid, 2)

    # Checks whether the student has a room.
    @property
    def is_allocated(self) -> bool:
        return bool(self.block and self.room)

