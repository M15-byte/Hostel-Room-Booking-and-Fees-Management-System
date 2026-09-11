"""
Handle student fee payments and payment history.
Each payment is saved so the system keeps a complete
record instead of only tracking the total amount paid.
"""

import math
from datetime import date

from models import Payment, Student


# Records one valid fee payment for a student.
def record_payment(student: Student, amount: float) -> bool:
    if not math.isfinite(amount) or amount <= 0:
        print("Payment failed. Amount must be greater than zero.")
        return False

    amount = round(amount, 2)
    if amount > student.balance:
        print(
            "Payment failed. Amount exceeds outstanding balance of "
            f"${student.balance:.2f}."
        )
        return False

    student.amount_paid = round(student.amount_paid + amount, 2)
    student.payments.append(
        Payment(amount=amount, date=date.today().isoformat())
    )

    print(f"Payment of ${amount:.2f} recorded for {student.name}.")
    print(f"Outstanding balance: ${student.balance:.2f}")
    return True


# Prints every payment made by a student.
def display_payment_history(student: Student) -> None:
    print(f"\nPayment history for {student.name} ({student.reg_no}):")

    if not student.payments:
        print("No payments made yet.")
        return

    for index, payment in enumerate(student.payments, start=1):
        print(f"Payment {index}: ${payment.amount:.2f} on {payment.date}")

    print(f"Total paid: ${student.amount_paid:.2f}")
    print(f"Outstanding: ${student.balance:.2f}")
