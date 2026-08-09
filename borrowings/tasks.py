from celery import shared_task
from django.utils import timezone

from borrowings.models import Borrowing
from borrowings.telegram_notifications import send_telegram_message


def get_overdue_borrowings():
    """Return borrowings that are overdue and not yet returned."""
    today = timezone.now().date()

    return Borrowing.objects.filter(
        expected_return_date__lt=today,
        actual_return_date__isnull=True,
    ).select_related("book", "user")


@shared_task
def check_overdue_borrowings():
    """Celery task: detect overdue borrowings (notification logic added next)."""
    overdue_borrowings = get_overdue_borrowings()
    return overdue_borrowings.count()
