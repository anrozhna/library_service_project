from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase

from payments.models import Payment
from payments.stripe_utils import (
    calculate_borrowing_total_price,
    create_stripe_session,
)
from tests_helpers import (
    sample_user,
    sample_book,
    sample_borrowing,
)


class CalculateBorrowingTotalPriceTests(TestCase):
    def setUp(self):
        self.user = sample_user()
        self.book = sample_book(daily_fee=Decimal("2.00"))

    def test_calculates_price_for_multiple_days(self):
        borrowing = sample_borrowing(
            self.user, self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

        result = calculate_borrowing_total_price(borrowing)

        self.assertEqual(result, Decimal("14.00"))

    def test_minimum_one_day_charged(self):
        borrowing = sample_borrowing(
            self.user, self.book,
            expected_return_date=date.today(),
        )

        result = calculate_borrowing_total_price(borrowing)

        self.assertEqual(result, Decimal("2.00"))


class CreateStripeSessionTests(TestCase):
    def setUp(self):
        self.user = sample_user()
        self.book = sample_book(daily_fee=Decimal("2.00"))
        self.borrowing = sample_borrowing(
            self.user, self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )

    @patch("payments.stripe_utils.stripe.checkout.Session.create")
    def test_creates_payment_with_session_data(self, mock_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_123456"
        mock_session.url = "https://checkout.stripe.com/test-session"
        mock_create.return_value = mock_session

        payment = create_stripe_session(
            self.borrowing,
            success_url="http://testserver/payments/success/",
            cancel_url="http://testserver/payments/cancel/",
        )

        self.assertEqual(payment.session_id, "cs_test_123456")
        self.assertEqual(
            payment.session_url,
            "https://checkout.stripe.com/test-session"
        )
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)
        self.assertEqual(payment.type, Payment.TypeChoices.PAYMENT)
        self.assertEqual(payment.borrowing, self.borrowing)
        self.assertEqual(payment.money_to_pay, Decimal("14.00"))

    @patch("payments.stripe_utils.stripe.checkout.Session.create")
    def test_calls_stripe_with_correct_amount(self, mock_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_123456"
        mock_session.url = "https://checkout.stripe.com/test-session"
        mock_create.return_value = mock_session

        create_stripe_session(
            self.borrowing,
            success_url="http://testserver/payments/success/",
            cancel_url="http://testserver/payments/cancel/",
        )

        called_kwargs = mock_create.call_args.kwargs
        unit_amount = called_kwargs["line_items"][0]["price_data"]["unit_amount"]

        self.assertEqual(unit_amount, 1400)  # $14.00 in cents

    @patch("payments.stripe_utils.stripe.checkout.Session.create")
    def test_payment_saved_to_database(self, mock_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_123456"
        mock_session.url = "https://checkout.stripe.com/test-session"
        mock_create.return_value = mock_session

        create_stripe_session(
            self.borrowing,
            success_url="http://testserver/payments/success/",
            cancel_url="http://testserver/payments/cancel/",
        )

        self.assertTrue(
            Payment.objects.filter(borrowing=self.borrowing).exists()
        )
