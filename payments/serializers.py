from rest_framework import serializers

from payments.models import Payment


class PaymentListSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.IntegerField(source="borrowing.id", read_only=True)
    book_title = serializers.CharField(
        source="borrowing.book.title", read_only=True
    )

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
