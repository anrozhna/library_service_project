import threading
from datetime import date, timedelta

from django.db import connections
from django.test import TransactionTestCase

from borrowings.models import Borrowing
from tests_helpers import sample_user, sample_book


class ConcurrentBorrowingCreationTests(TransactionTestCase):
    """
    Uses TransactionTestCase (not TestCase) because select_for_update()
    requires real, separate database transactions to actually block —
    the default TestCase wraps each test in a single outer transaction,
    which would prevent genuine concurrency from being tested.
    """

    def setUp(self):
        self.book = sample_book(inventory=1)  # only one copy available

    def _create_borrowing(self, user, results, index):
        from borrowings.serializers import BorrowingCreateSerializer

        try:
            serializer = BorrowingCreateSerializer(
                data={
                    "book": self.book.id,
                    "expected_return_date": (
                        date.today() + timedelta(days=7)
                    ).isoformat(),
                }
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            results[index] = "success"
        except Exception as e:
            results[index] = f"failed: {e}"
        finally:
            connections.close_all()

    def test_only_one_borrowing_succeeds_for_last_copy(self):
        user1 = sample_user(email="user1@test.com")
        user2 = sample_user(email="user2@test.com")

        results = [None, None]

        thread1 = threading.Thread(
            target=self._create_borrowing, args=(user1, results, 0)
        )
        thread2 = threading.Thread(
            target=self._create_borrowing, args=(user2, results, 1)
        )

        thread1.start()
        thread2.start()
        thread1.join()
        thread2.join()

        successes = [r for r in results if r == "success"]
        failures = [r for r in results if r and r.startswith("failed")]

        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)

        self.book.refresh_from_db()
        self.assertEqual(self.book.inventory, 0)

        self.assertEqual(Borrowing.objects.count(), 1)
