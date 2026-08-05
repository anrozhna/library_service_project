from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from books.models import Book
from books.serializers import BookSerializer

BOOKS_URL = reverse("books:book-list")

def detail_url(book_id):
    return reverse(
        "books:book-detail",
        kwargs={"pk": book_id}
    )

def sample_book(**params):
    defaults = {
        "title": "Sample Book",
        "author": "Sample Author",
        "cover": Book.CoverChoices.SOFT,
        "inventory": 5,
        "daily_fee": Decimal("1.50"),
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class UnauthenticatedBookAPITests(APITestCase):
    def setUp(self):
        self.book = sample_book()

    def test_book_list(self):
        response = self.client.get(BOOKS_URL)
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(len(response.data), 1)

    def test_book_retrieve(self):
        response = self.client.get(detail_url(self.book.id))
        serializer = BookSerializer(self.book)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_auth_required_for_book_create(self):
        data = {
            "title": "New Book",
            "author": "New Author",
            "cover": Book.CoverChoices.HARD,
            "inventory": 4,
            "daily_fee": Decimal("2.75"),
        }

        response = self.client.post(BOOKS_URL, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_required_for_book_update(self):
        response = self.client.patch(
            detail_url(self.book.id),
            {"title": "Updated Title"}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class AuthenticatedBookAPITests(APITestCase):
    def setUp(self):
        self.book = sample_book()
        self.user = get_user_model().objects.create_superuser(
            email="test@test.com",
            password="TestPass12345",
        )
        self.client.force_authenticate(self.user)

    def test_book_create(self):
        data = {
            "title": "New Book",
            "author": "New Author",
            "cover": Book.CoverChoices.HARD,
            "inventory": 4,
            "daily_fee": Decimal("2.75"),
        }

        response = self.client.post(BOOKS_URL, data)

        book = Book.objects.get(id=response.data["id"])
        serializer = BookSerializer(book)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data, serializer.data)
        self.assertEqual(Book.objects.count(), 2)

    def test_book_update(self):
        response = self.client.patch(
            detail_url(self.book.id),
            {"title": "Updated Title"}
        )

        self.book.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")
        self.assertEqual(self.book.title, "Updated Title")
