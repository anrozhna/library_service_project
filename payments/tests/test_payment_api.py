from datetime import date, timedelta
from decimal import Decimal

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from borrowings.models import Borrowing
from payments.models import Payment
from tests_helpers import sample_user, sample_book, sample_superuser

PAYMENTS_URL = reverse("payments:payment-list")


def detail_url(payment_id):
    return reverse("payments:payment-detail", kwargs={"pk": payment_id})


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
        "money_to_pay": Decimal("14.00"),
    }
    defaults.update(params)
    return Payment.objects.create(**defaults)


class UnauthenticatedPaymentApiTests(APITestCase):
    def test_auth_required(self):
        response = self.client.get(PAYMENTS_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatePaymentApiTests(APITestCase):
    def setUp(self):
        self.user = sample_user(email="user@test.com")
        self.client.force_authenticate(self.user)

        self.book = sample_book()
        self.borrowing = sample_borrowing(self.user, self.book)
        self.payment = sample_payment(self.borrowing)

    def test_list_only_own_payments(self):
        other_user = sample_user(email="other@test.com")
        other_borrowing = sample_borrowing(other_user, self.book)
        sample_payment(other_borrowing)

        response = self.client.get(PAYMENTS_URL)

        payment_ids = [p["id"] for p in response.data]
        self.assertIn(self.payment.id, payment_ids)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_own_payment(self):
        response = self.client.get(detail_url(self.payment.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.payment.id)

    def test_cannot_retrieve_other_user_payment(self):
        other_user = sample_user(email="other@test.com")
        other_borrowing = sample_borrowing(other_user, self.book)
        other_payment = sample_payment(other_borrowing)

        response = self.client.get(detail_url(other_payment.id))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminPaymentApiTests(APITestCase):
    def setUp(self):
        self.admin = sample_superuser(email="admin@test.com")
        self.client.force_authenticate(self.admin)

        self.book = sample_book()
        self.user1 = sample_user(email="u1@test.com")
        self.user2 = sample_user(email="u2@test.com")

        self.borrowing1 = sample_borrowing(self.user1, self.book)
        self.borrowing2 = sample_borrowing(self.user2, self.book)

        self.payment1 = sample_payment(self.borrowing1)
        self.payment2 = sample_payment(self.borrowing2)

    def test_admin_can_view_all_payments(self):
        response = self.client.get(PAYMENTS_URL)

        payment_ids = [p["id"] for p in response.data]
        self.assertIn(self.payment1.id, payment_ids)
        self.assertIn(self.payment2.id, payment_ids)
        self.assertEqual(len(response.data), 2)

    def test_admin_can_retrieve_any_payment(self):
        response = self.client.get(detail_url(self.payment2.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.payment2.id)
