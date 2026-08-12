import stripe
from django.conf import settings

from payments.models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


def calculate_borrowing_total_price(borrowing):
    """Calculate the total price for a borrowing based on its duration."""
    days_to_pay = (borrowing.expected_return_date - borrowing.borrow_date).days
    days_to_pay = max(1, days_to_pay)

    return days_to_pay * borrowing.book.daily_fee


def create_stripe_session(borrowing, success_url, cancel_url):
    """Create a Stripe Checkout Session for a given borrowing."""
    total_price = calculate_borrowing_total_price(borrowing)
    unit_amount = int(total_price * 100)  # Stripe expects the amount in cents

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"Borrowing of '{borrowing.book.title}'",
                    },
                    "unit_amount": unit_amount,
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
    )

    payment = Payment.objects.create(
        status=Payment.StatusChoices.PENDING,
        type=Payment.TypeChoices.PAYMENT,
        borrowing=borrowing,
        session_url=session.url,
        session_id=session.id,
        money_to_pay=total_price,
    )

    return payment
