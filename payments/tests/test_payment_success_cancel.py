from datetime import date, timedelta
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from payments.models import Payment
from tests_helpers import (
    sample_user,
    sample_book,
    sample_borrowing,
    sample_payment,
    mock_stripe_session,
)

SUCCESS_URL = reverse("payments:payment-success")
CANCEL_URL = reverse("payments:payment-cancel")


class PaymentSuccessEndpointTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)

        self.book = sample_book()
        self.borrowing = sample_borrowing(
            self.user, self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.payment = sample_payment(self.borrowing)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_marks_payment_as_paid_when_stripe_confirms(self, mock_retrieve):
        mock_retrieve.return_value = mock_stripe_session(payment_status="paid")

        response = self.client.get(
            SUCCESS_URL, {"session_id": self.payment.session_id}
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PAID)
        mock_retrieve.assert_called_once_with(self.payment.session_id)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_does_not_mark_paid_when_stripe_says_unpaid(self, mock_retrieve):
        mock_retrieve.return_value = mock_stripe_session(payment_status="unpaid")

        response = self.client.get(
            SUCCESS_URL, {"session_id": self.payment.session_id}
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_handles_stripe_error_gracefully(self, mock_retrieve):
        import stripe

        mock_retrieve.side_effect = stripe.error.StripeError("network error")

        response = self.client.get(
            SUCCESS_URL, {"session_id": self.payment.session_id}
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)

    def test_success_without_session_id_returns_400(self):
        response = self.client.get(SUCCESS_URL)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_success_with_unknown_session_id_returns_404(self):
        response = self.client.get(
            SUCCESS_URL, {"session_id": "cs_test_does_not_exist"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_success_called_twice_does_not_recheck_stripe(self, mock_retrieve):
        mock_retrieve.return_value = mock_stripe_session(payment_status="paid")

        self.client.get(SUCCESS_URL, {"session_id": self.payment.session_id})
        response = self.client.get(
            SUCCESS_URL, {"session_id": self.payment.session_id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Stripe should only be called once — the second call short-circuits
        # because the payment is already PAID
        self.assertEqual(mock_retrieve.call_count, 1)


class PaymentOwnershipTests(APITestCase):
    """Ensure users cannot confirm or view other users' payments."""

    def setUp(self):
        self.owner = sample_user(email="owner@test.com")
        self.other_user = sample_user(email="other@test.com")
        self.client.force_authenticate(self.other_user)

        self.book = sample_book()
        self.borrowing = sample_borrowing(
            self.owner, self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.payment = sample_payment(self.borrowing)

    @patch("payments.views.stripe.checkout.Session.retrieve")
    def test_cannot_confirm_another_users_payment(self, mock_retrieve):
        mock_retrieve.return_value = mock_stripe_session(payment_status="paid")

        response = self.client.get(
            SUCCESS_URL, {"session_id": self.payment.session_id}
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)
        mock_retrieve.assert_not_called()

    def test_cancel_does_not_leak_another_users_session_url(self):
        response = self.client.get(
            CANCEL_URL, {"session_id": self.payment.session_id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("session_url", response.data)


class PaymentCancelEndpointTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)

        self.book = sample_book()
        self.borrowing = sample_borrowing(
            self.user, self.book,
            expected_return_date=date.today() + timedelta(days=7),
        )
        self.payment = sample_payment(self.borrowing)

    def test_cancel_returns_session_url_for_own_payment(self):
        response = self.client.get(
            CANCEL_URL, {"session_id": self.payment.session_id}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["session_url"], self.payment.session_url)

    def test_cancel_does_not_change_payment_status(self):
        response = self.client.get(
            CANCEL_URL, {"session_id": self.payment.session_id}
        )

        self.payment.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.payment.status, Payment.StatusChoices.PENDING)

    def test_cancel_without_session_id_returns_generic_message(self):
        response = self.client.get(CANCEL_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("session_url", response.data)
