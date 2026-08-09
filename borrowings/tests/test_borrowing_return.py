from datetime import date, timedelta

from rest_framework import status
from rest_framework.test import APITestCase

from borrowings.models import Borrowing
from borrowings.tests.helpers import return_url
from tests_helpers import sample_user, sample_book


class BorrowingReturnApiTests(APITestCase):
    def setUp(self):
        self.user = sample_user()
        self.client.force_authenticate(self.user)

        self.book = sample_book(inventory=2)

        self.borrowing = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

    def test_return_borrowing_success(self):
        response = self.client.post(return_url(self.borrowing.id))

        self.borrowing.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(self.borrowing.actual_return_date)
        self.assertEqual(self.borrowing.actual_return_date, date.today())

    def test_return_borrowing_increases_book_inventory(self):
        self.client.post(return_url(self.borrowing.id))

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 3)

    def test_cannot_return_borrowing_twice(self):
        self.client.post(return_url(self.borrowing.id))
        response = self.client.post(return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_second_return_does_not_increase_inventory_again(self):
        self.client.post(return_url(self.borrowing.id))
        self.client.post(return_url(self.borrowing.id))

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 3)

    def test_unauthenticated_user_cannot_return_borrowing(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(return_url(self.borrowing.id))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
