from datetime import date, timedelta
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from borrowings.tests.helpers import BORROWINGS_URL
from tests_helpers import (
    sample_user,
    sample_superuser,
    sample_book,
    sample_borrowing,
    sample_payment,
)
from payments.models import Payment


class PendingPaymentBlockTests(APITestCase):
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

    def test_cannot_create_borrowing_with_pending_payment(self):
        other_book = sample_book(inventory=2)
        existing_borrowing = sample_borrowing(self.user, other_book)
        sample_payment(existing_borrowing, status=Payment.StatusChoices.PENDING)

        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_create_borrowing_when_all_payments_are_paid(self):
        other_book = sample_book(inventory=2)
        existing_borrowing = sample_borrowing(self.user, other_book)
        sample_payment(existing_borrowing, status=Payment.StatusChoices.PAID)

        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_create_borrowing_with_no_prior_payments(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_pending_payment_of_other_user_does_not_block(self):
        other_user = sample_user(email="other@test.com")
        other_book = sample_book(inventory=2)
        other_borrowing = sample_borrowing(other_user, other_book)
        sample_payment(other_borrowing, status=Payment.StatusChoices.PENDING)

        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class AdminPendingPaymentBlockTests(APITestCase):
    def setUp(self):
        self.telegram_patcher = patch("borrowings.views.send_telegram_message")
        self.mock_send_telegram_message = self.telegram_patcher.start()
        self.addCleanup(self.telegram_patcher.stop)

        self.stripe_patcher = patch("borrowings.views.create_stripe_session")
        self.mock_create_stripe_session = self.stripe_patcher.start()
        self.addCleanup(self.stripe_patcher.stop)

        self.admin = sample_superuser()
        self.client.force_authenticate(self.admin)
        self.target_user = sample_user(email="target@test.com")
        self.book = sample_book(inventory=3)

    def test_admin_blocked_when_target_user_has_pending_payment(self):
        other_book = sample_book(inventory=2)
        existing_borrowing = sample_borrowing(self.target_user, other_book)
        sample_payment(existing_borrowing, status=Payment.StatusChoices.PENDING)

        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
            "user": self.target_user.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_create_for_user_without_pending_payments(self):
        payload = {
            "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
            "book": self.book.id,
            "user": self.target_user.id,
        }
        response = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
