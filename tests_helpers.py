from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

from django.contrib.auth import get_user_model

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment


def sample_user(**params):
    defaults = {
        "email": "user@test.com",
        "password": "testpass123",
    }
    defaults.update(params)
    return get_user_model().objects.create_user(**defaults)


def sample_superuser(**params):
    defaults = {
        "email": "admin@test.com",
        "password": "adminpass123",
    }
    defaults.update(params)
    return get_user_model().objects.create_superuser(**defaults)


def sample_book(**params):
    defaults = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "cover": Book.CoverChoices.SOFT,
        "inventory": 5,
        "daily_fee": Decimal("2.00"),
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


def sample_borrowing(user, book, **params):
    defaults = {
        "borrow_date": date.today(),
        "expected_return_date": date.today() + timedelta(days=7),
        "book": book,
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def sample_payment(borrowing, **params):
    defaults = {
        "status": Payment.StatusChoices.PENDING,
        "type": Payment.TypeChoices.PAYMENT,
        "borrowing": borrowing,
        "session_id": "cs_test_sample123",
        "session_url": "https://checkout.stripe.com/test-session",
        "money_to_pay": Decimal("14.00"),
    }
    defaults.update(params)
    return Payment.objects.create(**defaults)


def mock_stripe_session(payment_status="paid"):
    """Build a MagicMock imitating a Stripe checkout.Session response."""
    mock_session = MagicMock()
    mock_session.payment_status = payment_status
    return mock_session
