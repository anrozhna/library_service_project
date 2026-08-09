from rest_framework.reverse import reverse

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", kwargs={"pk": borrowing_id})


def return_url(borrowing_id):
    return f"/borrowings/{borrowing_id}/return/"
