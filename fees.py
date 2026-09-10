"""
fees.py

Applies fee payments to a student's account and keeps a full payment
history, rather than just a single running total. Keeping the history
means a defaulter dispute ("I definitely paid last month") can be
answered by looking at the record instead of taking anyone's word for it.
"""

from datetime import date
from models import Student, Payment


def record_payment(student: Student, amount: float) -> bool:
    """
    Applies a single payment to a student's account.

    Two conditions are rejected before anything is changed:
    an amount that isn't positive, and an amount bigger than what's
    actually owed. Both are checked up front so a rejected payment
    never partially updates the student's record.
    """
    if amount <= 0:
        print("Payment failed. Amount must be greater than zero.")
        return False

    if amount > student.balance:
        print(f"Payment failed. Amount exceeds outstanding balance of ${student.balance}.")
        return False

    student.amount_paid = round(student.amount_paid + amount, 2)
    student.payments.append(Payment(amount=amount, date=str(date.today())))

    print(f"Payment of ${amount} recorded for {student.name}.")
    print(f"Outstanding balance: ${student.balance}")
    return True


def display_payment_history(student: Student) -> None:
    print(f"\nPayment history for {student.name} ({student.reg_no}):")
    if not student.payments:
        print("No payments made yet.")
        return

    for index, payment in enumerate(student.payments, start=1):
        print(f"Payment {index}: ${payment.amount}  on {payment.date}")

    print(f"Total paid: ${student.amount_paid}")
    print(f"Outstanding: ${student.balance}")
