from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase

from payments.models import Payment
from payments.stripe_utils import calculate_fine_amount, create_fine_payment
from tests_helpers import (
    sample_user,
    sample_book,
    sample_borrowing,
)


class CalculateFineAmountTests(TestCase):
    def setUp(self):
        self.user = sample_user()
        self.book = sample_book(daily_fee=Decimal("2.00"))

    def test_calculates_fine_for_overdue_days(self):
        borrowing = sample_borrowing(
            self.user,
            self.book,
            expected_return_date=date.today() - timedelta(days=5),
            actual_return_date=date.today(),
        )

        result = calculate_fine_amount(borrowing)

        # 5 overdue days * $2.00 daily_fee * FINE_MULTIPLIER (2) = $20.00
        self.assertEqual(result, Decimal("20.00"))

    def test_minimum_one_day_fine(self):
        borrowing = sample_borrowing(
            self.user,
            self.book,
            expected_return_date=date.today(),
            actual_return_date=date.today(),
        )

        result = calculate_fine_amount(borrowing)

        # even same-day overdue counts as at least 1 day
        self.assertEqual(result, Decimal("4.00"))  # 1 * 2.00 * 2


class CreateFinePaymentTests(TestCase):
    def setUp(self):
        self.user = sample_user()
        self.book = sample_book(daily_fee=Decimal("2.00"))
        self.borrowing = sample_borrowing(
            self.user,
            self.book,
            expected_return_date=date.today() - timedelta(days=5),
            actual_return_date=date.today(),
        )

    @patch("payments.stripe_utils.stripe.checkout.Session.create")
    def test_creates_fine_payment_with_correct_type(self, mock_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_fine123"
        mock_session.url = "https://checkout.stripe.com/fine-session"
        mock_create.return_value = mock_session

        payment = create_fine_payment(
            self.borrowing,
            success_url="http://testserver/payments/success/",
            cancel_url="http://testserver/payments/cancel/",
        )

        self.assertEqual(payment.type, Payment.TypeChoices.FINE)
        self.assertEqual(payment.status, Payment.StatusChoices.PENDING)
        self.assertEqual(payment.money_to_pay, Decimal("20.00"))
        self.assertEqual(payment.session_id, "cs_test_fine123")

    @patch("payments.stripe_utils.stripe.checkout.Session.create")
    def test_calls_stripe_with_correct_fine_amount(self, mock_create):
        mock_session = MagicMock()
        mock_session.id = "cs_test_fine123"
        mock_session.url = "https://checkout.stripe.com/fine-session"
        mock_create.return_value = mock_session

        create_fine_payment(
            self.borrowing,
            success_url="http://testserver/payments/success/",
            cancel_url="http://testserver/payments/cancel/",
        )

        called_kwargs = mock_create.call_args.kwargs
        unit_amount = called_kwargs["line_items"][0]["price_data"]["unit_amount"]

        self.assertEqual(unit_amount, 2000)  # $20.00 in cents


class ReturnBorrowingCreatesFineTests(TestCase):
    """Integration-level tests for fine creation during borrowing return."""

    def setUp(self):
        self.user = sample_user()
        self.book = sample_book(daily_fee=Decimal("2.00"), inventory=2)

    @patch("borrowings.views.create_fine_payment")
    def test_overdue_return_triggers_fine_payment(self, mock_create_fine):
        from rest_framework.test import APIClient
        from borrowings.models import Borrowing

        client = APIClient()
        client.force_authenticate(self.user)

        borrowing = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=15),
            expected_return_date=date.today() - timedelta(days=5),
            book=self.book,
            user=self.user,
        )

        from borrowings.tests.helpers import return_url

        client.post(return_url(borrowing.id))

        mock_create_fine.assert_called_once()

    @patch("borrowings.views.create_fine_payment")
    def test_on_time_return_does_not_trigger_fine_payment(self, mock_create_fine):
        from rest_framework.test import APIClient
        from borrowings.models import Borrowing

        client = APIClient()
        client.force_authenticate(self.user)

        borrowing = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=5),
            expected_return_date=date.today() + timedelta(days=2),
            book=self.book,
            user=self.user,
        )

        from borrowings.tests.helpers import return_url

        client.post(return_url(borrowing.id))

        mock_create_fine.assert_not_called()
