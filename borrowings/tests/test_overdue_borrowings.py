from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from borrowings.models import Borrowing
from borrowings.tasks import get_overdue_borrowings, check_overdue_borrowings
from borrowings.tests.helpers import sample_book, sample_user


class GetOverdueBorrowingsTests(TestCase):
    def setUp(self):
        self.user = sample_user()
        self.book = sample_book()

    def test_overdue_borrowing_is_detected(self):
        overdue = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            book=self.book,
            user=self.user,
        )

        result = get_overdue_borrowings()

        self.assertIn(overdue, result)

    def test_not_yet_due_borrowing_is_not_detected(self):
        not_due = Borrowing.objects.create(
            borrow_date=date.today(),
            expected_return_date=date.today() + timedelta(days=7),
            book=self.book,
            user=self.user,
        )

        result = get_overdue_borrowings()

        self.assertNotIn(not_due, result)

    def test_already_returned_borrowing_is_not_detected(self):
        returned = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            actual_return_date=date.today() - timedelta(days=1),
            book=self.book,
            user=self.user,
        )

        result = get_overdue_borrowings()

        self.assertNotIn(returned, result)

    def test_borrowing_due_today_is_not_overdue(self):
        due_today = Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=7),
            expected_return_date=date.today(),
            book=self.book,
            user=self.user,
        )

        result = get_overdue_borrowings()

        self.assertNotIn(due_today, result)


class CheckOverdueBorrowingsTaskTests(TestCase):
    def setUp(self):
        self.user = sample_user()
        self.book = sample_book()

    @patch("borrowings.tasks.send_telegram_message")
    def test_sends_notification_for_each_overdue_borrowing(self, mock_send):
        Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=10),
            expected_return_date=date.today() - timedelta(days=1),
            book=self.book,
            user=self.user,
        )
        Borrowing.objects.create(
            borrow_date=date.today() - timedelta(days=15),
            expected_return_date=date.today() - timedelta(days=5),
            book=self.book,
            user=self.user,
        )

        result = check_overdue_borrowings()

        self.assertEqual(mock_send.call_count, 2)
        self.assertEqual(result, 2)

    @patch("borrowings.tasks.send_telegram_message")
    def test_sends_no_overdue_message_when_list_is_empty(self, mock_send):
        result = check_overdue_borrowings()

        mock_send.assert_called_once_with("No borrowings overdue today!")
        self.assertEqual(result, 0)
