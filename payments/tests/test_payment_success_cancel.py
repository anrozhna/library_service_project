from datetime import date, timedelta

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.models import Payment
from tests_helpers import (
    sample_user,
    sample_book,
    sample_borrowing,
    sample_payment,
)

SUCCESS_URL = reverse("payments:payment-success")
CANCEL_URL = reverse("payments:payment-cancel")


class PaymentSuccessEndpointTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)

        self.book = sample_book()
        self.borrowing = sample_borrowing(
            self.user,
            self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.payment = sample_payment(self.borrowing)

    def test_success_marks_payment_as_paid(self):
        response = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)

    def test_success_without_session_id_returns_400(self):
        response = self.client.get(SUCCESS_URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_success_with_unknown_session_id_returns_404(self):
        response = self.client.get(
            SUCCESS_URL, {"session_id": "cs_test_does_not_exist"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_success_called_twice_does_not_error(self):
        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})
        response = self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)


class PaymentCancelEndpointTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)

        self.book = sample_book()
        self.borrowing = sample_borrowing(
            self.user,
            self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.payment = sample_payment(self.borrowing)

    def test_cancel_returns_200_and_does_not_change_payment_status(self):
        response = self.client.get(CANCEL_URL)

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)
