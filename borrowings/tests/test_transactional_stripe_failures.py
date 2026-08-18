from datetime import date, timedelta
from unittest.mock import patch

import stripe
from rest_framework import status
from rest_framework.test import APITestCase

from borrowings.models import Borrowing
from borrowings.tests.helpers import BORROWINGS_URL, return_url
from tests_helpers import sample_user, sample_book


class BorrowingCreateStripeFailureTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.book = sample_book(inventory=3)

    @patch("borrowings.views.create_stripe_session")
    def test_borrowing_not_created_when_stripe_fails(self, mock_create_session):
        mock_create_session.side_effect = stripe.error.StripeError("Stripe is down")

        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(Borrowing.objects.filter(book=self.book).exists())

    @patch("borrowings.views.create_stripe_session")
    def test_book_inventory_not_decreased_when_stripe_fails(self, mock_create_session):
        mock_create_session.side_effect = stripe.error.StripeError("Stripe is down")

        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        self.client.post(BORROWINGS_URL, payload)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 3)  # unchanged

    @patch("borrowings.views.create_stripe_session")
    def test_telegram_not_sent_when_stripe_fails(self, mock_create_session):
        with patch("borrowings.views.send_telegram_message") as mock_telegram:
            mock_create_session.side_effect = stripe.error.StripeError("Stripe is down")

            payload = {
                "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
                "book": self.book.id,
            }
            self.client.post(BORROWINGS_URL, payload)

            mock_telegram.assert_not_called()


class BorrowingReturnFineStripeFailureTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.book = sample_book(inventory=2)

        self.borrowing = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=15),
            expected_return_date=date.today() - timedelta(days=5),
            book=self.book,
            user=self.user,
        )

    @patch("borrowings.views.create_fine_payment")
    def test_return_rolled_back_when_fine_payment_fails(self, mock_create_fine):
        mock_create_fine.side_effect = stripe.error.StripeError("Stripe is down")

        response = self.client.post(return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

        self.borrowing.refresh_from_db()
        self.book.refresh_from_db()

        # Neither the return nor the inventory increase should have persisted
        self.assertIsNone(self.borrowing.actual_return_date)
        self.assertEqual(self.book.inventory, 2)

    def test_on_time_return_does_not_call_fine_payment(self):
        self.borrowing.expected_return_date = date.today() + timedelta(days=5)
        self.borrowing.save()

        with patch("borrowings.views.create_fine_payment") as mock_create_fine:
            response = self.client.post(return_url(self.borrowing.id))

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_create_fine.assert_not_called()
