from rest_framework import serializers

from borrowings.serializers import BorrowingListSerializer
from payments.models import Payment


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.IntegerField(source="borrowing.id", read_only=True)
    book_title = serializers.CharField(source="borrowing.book.title", read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing_id",
            "book_title",
            "money_to_pay",
        )
        read_only_fields = fields


class PaymentDetailSerializer(serializers.ModelSerializer):
    borrowing = BorrowingListSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "session_url",
            "session_id",
            "money_to_pay",
        )
        read_only_fields = fields
