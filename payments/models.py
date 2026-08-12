from django.db import models

from borrowings.models import Borrowing


class Payment(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PAID = "PAID", "Paid"

    class TypeChoices(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    type = models.CharField(
        max_length=10,
        choices=TypeChoices.choices,
        default=TypeChoices.PAYMENT,
    )
    borrowing = models.ForeignKey(
        Borrowing,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    session_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )
    session_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    money_to_pay = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    def __str__(self):
        return (
            f"{self.type} payment for borrowing "
            f"#{self.borrowing_id} - {self.status}"
        )
