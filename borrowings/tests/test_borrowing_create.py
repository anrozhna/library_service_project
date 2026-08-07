from datetime import date, timedelta
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from borrowings.models import Borrowing
from borrowings.tests.helpers import (
    sample_book,
    BORROWINGS_URL,
    sample_user
)


class BorrowingCreateApiTests(APITestCase):
    def setUp(self):
        self.telegram_patcher = patch(
            "borrowings.views.send_telegram_message"
        )
        self.mock_send_telegram_message = self.telegram_patcher.start()
        self.addCleanup(self.telegram_patcher.stop)

        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.book = sample_book(inventory=3)

    def test_create_borrowing_success(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Borrowing.objects.filter(book=self.book, user=self.user).exists()
        )

    def test_create_borrowing_decreases_book_inventory(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        self.client.post(BORROWINGS_URL, payload)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 2)

    def test_create_borrowing_attaches_current_user(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)
        borrowing = Borrowing.objects.get(id=response.data["id"])
        self.assertEqual(borrowing.user, self.user)

    def test_create_borrowing_with_zero_inventory_fails(self):
        book = sample_book(inventory=0)
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_borrowing_does_not_decrease_inventory_on_failure(self):
        book = sample_book(inventory=0)
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": book.id,
        }
        self.client.post(BORROWINGS_URL, payload)

        book.refresh_from_db()
        self.assertEqual(book.inventory, 0)

    def test_create_borrowing_sends_telegram_message(self):
        payload = {
            "book": self.book.id,
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
        }

        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        borrowing = Borrowing.objects.get(id=response.data["id"])

        expected_message = (
            f"📚 New borrowing created!\n"
            f"Book: {borrowing.book.title}\n"
            f"User: {borrowing.user.email}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )

        self.mock_send_telegram_message.assert_called_once_with(expected_message)

    def test_create_borrowing_does_not_send_telegram_on_failure(self):
        book = sample_book(inventory=0)

        payload = {
            "book": book.id,
            "expected_return_date": (
                    date.today() + timedelta(days=7)
            ).isoformat(),
        }

        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.mock_send_telegram_message.assert_not_called()
