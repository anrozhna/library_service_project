# payments/stripe_utils.py
from decimal import Decimal

import stripe
from django.conf import settings

from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_borrowing_total_price(borrowing):
    """Calculate the total price for a borrowing based on its duration."""
    days_to_pay = (borrowing.expected_return_date - borrowing.borrow_date).days
    days_to_pay = max(1, days_to_pay)

    return days_to_pay * borrowing.book.daily_fee


def calculate_fine_amount(borrowing):
    """Calculate the fine amount for an overdue return."""
    overdue_days = (borrowing.actual_return_date - borrowing.expected_return_date).days
    overdue_days = max(overdue_days, 1)

    fine_multiplier = Decimal(str(settings.FINE_MULTIPLIER))

    return overdue_days * borrowing.book.daily_fee * fine_multiplier


def _create_checkout_session(borrowing, amount, product_name, success_url, cancel_url):
    """Shared helper to create a Stripe Checkout Session for a given amount."""
    unit_amount = int(amount * 100)

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": product_name},
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        metadata={"borrowing_id": str(borrowing.id)},
    )


def create_stripe_session(borrowing, success_url, cancel_url):
    """Create a Stripe Checkout Session for a borrowing and save it as a Payment."""
    total_price = calculate_borrowing_total_price(borrowing)
    session = _create_checkout_session(
        borrowing,
        total_price,
        f"Borrowing of '{borrowing.book.title}'",
        success_url,
        cancel_url,
    )

    return Payment.objects.create(
        status=Payment.StatusChoices.PENDING,
        type=Payment.TypeChoices.PAYMENT,
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=total_price,
    )


def create_fine_payment(borrowing, success_url, cancel_url):
    """Create a Stripe Checkout Session and Payment for an overdue fine."""
    fine_amount = calculate_fine_amount(borrowing)
    session = _create_checkout_session(
        borrowing,
        fine_amount,
        f"Fine for overdue return of '{borrowing.book.title}'",
        success_url,
        cancel_url,
    )

    return Payment.objects.create(
        status=Payment.StatusChoices.PENDING,
        type=Payment.TypeChoices.FINE,
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=fine_amount,
    )
