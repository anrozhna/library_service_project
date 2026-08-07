from rest_framework.reverse import reverse

from books.models import Book

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", kwargs={"pk": borrowing_id})


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


def return_url(borrowing_id):
    return f"/borrowings/{borrowing_id}/return/"