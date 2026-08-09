from datetime import timedelta, date

from rest_framework import status
from rest_framework.test import APITestCase

from borrowings.models import Borrowing
from borrowings.tests.helpers import BORROWINGS_URL
from tests_helpers import (
    sample_book,
    sample_user,
    sample_superuser,
)


class BorrowingIsActiveFilterApiTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)
        self.book = sample_book()

        self.active_borrowing = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )
        self.returned_borrowing = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=3),
            actual_return_date=date.today() - timedelta(days=2),
            book=self.book,
            user=self.user,
        )

    def test_filter_by_is_active_true_returns_only_active(self):
        response = self.client.get(BORROWINGS_URL, {"is_active": "true"})

        ids = [record["id"] for record in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.active_borrowing.id, ids)
        self.assertNotIn(self.returned_borrowing.id, ids)

    def test_filter_by_is_active_false_returns_only_returned(self):
        response = self.client.get(BORROWINGS_URL, {"is_active": "false"})

        ids = [record["id"] for record in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.returned_borrowing.id, ids)
        self.assertNotIn(self.active_borrowing.id, ids)

    def test_no_is_active_filter_returns_all_own_borrowings(self):
        response = self.client.get(BORROWINGS_URL)

        ids = [b["id"] for b in response.data]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.active_borrowing.id, ids)
        self.assertIn(self.returned_borrowing.id, ids)
        self.assertEqual(len(response.data), 2)


class BorrowingUserIdFilterApiTests(APITestCase):
    def setUp(self):
        self.admin = sample_superuser()
        self.user1 = sample_user(email="u1@test.com")
        self.user2 = sample_user(email="u2@test.com")
        self.book = sample_book()
        self.borrowing1 = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user1,
        )
        self.borrowing2 = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user2,
        )

    def test_admin_can_filter_by_user_id(self):
        self.client.force_authenticate(self.admin)

        response = self.client.get(BORROWINGS_URL, {"user_id": self.user1.id})

        ids = [record["id"] for record in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.borrowing1.id, ids)
        self.assertNotIn(self.borrowing2.id, ids)

    def test_user_can_not_filter_by_user_id(self):
        self.client.force_authenticate(self.user1)

        response = self.client.get(BORROWINGS_URL, {"user_id": self.user2.id})

        ids = [record["id"] for record in response.data]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # user_id ignored for non-admins — only own borrowings returned
        self.assertIn(self.borrowing1.id, ids)
        self.assertNotIn(self.borrowing2.id, ids)
