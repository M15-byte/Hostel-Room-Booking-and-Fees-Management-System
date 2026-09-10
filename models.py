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
from typing import List, Optional


@dataclass
class Payment:
    """A single fee payment made by a student, timestamped when it happened."""
    amount: float
    date: str  # stored as an ISO date string (YYYY-MM-DD) so it serializes to JSON cleanly


@dataclass
class Room:
    """
    A single room inside a hostel block.

    capacity has no default value on purpose: every room in this system
    is created from information the warden actually enters at setup time,
    never from an assumed number, so there is nothing here to fall back on.
    """
    capacity: int
    occupants: List[str] = field(default_factory=list)  # list of registration numbers

    def is_full(self) -> bool:
        """A room is full once its occupant count reaches its capacity."""
        return len(self.occupants) >= self.capacity

    def has_space(self) -> bool:
        return not self.is_full()

    def occupancy_label(self) -> str:
        """Human-readable 'x/y - STATUS' string used in every report/listing."""
        status = "FULL" if self.is_full() else "AVAILABLE"
        return f"{len(self.occupants)}/{self.capacity} - {status}"


@dataclass
class Student:
    """
    A single registered student and everything tied to their hostel stay.

    total_fee is supplied per student at registration time rather than
    assumed to be some fixed amount, since real hostels charge different
    students differently (by course, by room type, by year of study, etc).
    """
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

    @property
    def balance(self) -> float:
        """Outstanding balance, always derived from total_fee and amount_paid
        rather than stored on its own, so the two numbers can never disagree."""
        return round(self.total_fee - self.amount_paid, 2)

    @property
    def is_allocated(self) -> bool:
        return bool(self.block) and bool(self.room)
