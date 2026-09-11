"""
Handle student fee payments and payment history.
Each payment is saved so the system keeps a complete
record instead of only tracking the total amount paid.
"""

from datetime import date
from models import Student, Payment


# Record a payment for a student
def record_payment(student: Student, amount: float) -> bool:

    # Reject invalid payment amounts
    if amount <= 0:
        print("Payment failed. Amount must be greater than zero.")
        return False

    if amount > student.balance:
        print(f"Payment failed. Amount exceeds outstanding balance of ${student.balance}.")
        return False

    # Update the student's payment details
    student.amount_paid = round(student.amount_paid + amount, 2)
    student.payments.append(Payment(amount=amount, date=str(date.today())))

    # Show confirmation
    print(f"Payment of ${amount} recorded for {student.name}.")
    print(f"Outstanding balance: ${student.balance}")
    return True


# Display all payments made by a student
def display_payment_history(student: Student) -> None:

    print(f"\nPayment history for {student.name} ({student.reg_no}):")

    if not student.payments:
        print("No payments made yet.")
        return

    # List every payment
    for index, payment in enumerate(student.payments, start=1):
        print(f"Payment {index}: ${payment.amount}  on {payment.date}")

    # Show payment summary
    print(f"Total paid: ${student.amount_paid}")
    print(f"Outstanding: ${student.balance}")


