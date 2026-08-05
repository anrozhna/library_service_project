from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingListSerializer,
    BorrowingDetailSerializer
)

BORROWINGS_URL = reverse("borrowings:borrowing-list")

def detail_url(borrowing_id):
    return reverse(
        "borrowings:borrowing-detail",
        kwargs={"pk": borrowing_id}
    )

def sample_book(**params):
    defaults = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "cover": Book.CoverChoices.SOFT,
        "inventory": 5,
        "daily_fee": "2.00",
    }
    defaults.update(params)

    return Book.objects.create(**defaults)


class PublicBorrowingApiTest(APITestCase):
    def test_auth_required(self):
        response = self.client.get(BORROWINGS_URL)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateBorrowingApiTest(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass123",
        )
        self.client.force_authenticate(self.user)

        self.book = sample_book()

        self.borrowing = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

    def test_list_only_own_borrowings(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testpass123",
        )

        Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=14),
            book=self.book,
            user=other_user,
        )

        response = self.client.get(BORROWINGS_URL)

        serializer = BorrowingListSerializer([self.borrowing], many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_own_borrowing(self):
        response = self.client.get(detail_url(self.borrowing.id))

        serializer = BorrowingDetailSerializer(self.borrowing)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_cannot_retrieve_other_user_borrowing(self):
        other_user = get_user_model().objects.create_user(
            email="other@test.com",
            password="testpass123",
        )

        borrowing = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=other_user,
        )

        response = self.client.get(detail_url(borrowing.id))

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AdminBorrowingApiTests(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            email="admin@test.com",
            password="adminpass123",
        )
        self.client.force_authenticate(self.admin)

        book = sample_book()

        user = get_user_model().objects.create_user(
            email="user@test.com",
            password="testpass123",
        )

        Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=book,
            user=user,
        )

    def test_admin_can_view_all_borrowings(self):
        response = self.client.get(BORROWINGS_URL)

        borrowings = Borrowing.objects.select_related(
            "book",
            "user",
        )

        serializer = BorrowingListSerializer(
            borrowings,
            many=True,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
