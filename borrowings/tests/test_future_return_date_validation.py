from datetime import date, timedelta
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from borrowings.tests.helpers import BORROWINGS_URL
from tests_helpers import sample_user, sample_book


class FutureReturnDateValidationTests(APITestCase):
    def setUp(self):
        self.telegram_patcher = patch("borrowings.views.send_telegram_message")
        self.mock_send_telegram_message = self.telegram_patcher.start()
        self.addCleanup(self.telegram_patcher.stop)

        self.stripe_patcher = patch("borrowings.views.create_stripe_session")
        self.mock_create_stripe_session = self.stripe_patcher.start()
        self.addCleanup(self.stripe_patcher.stop)

        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.book = sample_book(inventory=3)

    def test_cannot_create_borrowing_with_past_return_date(self):
        payload = {
            "expected_return_date": (date.today() - timedelta(days=1)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", response.data)

    def test_cannot_create_borrowing_with_today_date(self):
        payload = {
            "expected_return_date": date.today().isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", response.data)

    def test_can_create_borrowing_with_tomorrows_date(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=1)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_borrowing_with_far_future_date(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=30)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_past_date_does_not_decrease_inventory(self):
        payload = {
            "expected_return_date": (date.today() - timedelta(days=1)).isoformat(),
            "book": self.book.id,
        }
        self.client.post(BORROWINGS_URL, payload)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 3)

    def test_combined_invalid_book_and_date_returns_both_errors(self):
        out_of_stock_book = sample_book(inventory=0)

        payload = {
            "expected_return_date": (date.today() - timedelta(days=1)).isoformat(),
            "book": out_of_stock_book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book", response.data)
        self.assertIn("expected_return_date", response.data)
