from django.contrib.auth import get_user_model
from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing
from users.serializers import UserSerializer


class PaymentNestedSerializer(serializers.Serializer):
    """Lightweight payment representation nested inside
    Borrowing details to avoid circular imports."""

    id = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    session_url = serializers.URLField(read_only=True)
    money_to_pay = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )


class BorrowingSerializer(serializers.ModelSerializer):
    payments = PaymentNestedSerializer(
        read_only=True,
        many=True,
    )

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
            "payments",
        )


class BorrowingListSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.SlugRelatedField(read_only=True, slug_field="email")


class BorrowingDetailSerializer(BorrowingListSerializer):
    user = UserSerializer(read_only=True)


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "book", "expected_return_date")

    @staticmethod
    def validate_book(value):
        if value.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")
        return value

    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save()

        return Borrowing.objects.create(**validated_data)


class AdminBorrowingCreateSerializer(BorrowingCreateSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
    )

    class Meta(BorrowingCreateSerializer.Meta):
        fields = BorrowingCreateSerializer.Meta.fields + ("user",)
