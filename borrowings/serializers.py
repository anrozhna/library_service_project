from django.contrib.auth import get_user_model
from django.db import transaction

from rest_framework import serializers

from books.models import Book
from books.serializers import BookSerializer
from borrowings.models import Borrowing
from payments.models import Payment
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

    def validate(self, attrs):
        request = self.context.get("request")
        user = attrs.get("user") or (request.user if request else None)

        if (
            user
            and Payment.objects.filter(
                borrowing__user=user, status=Payment.StatusChoices.PENDING
            ).exists()
        ):
            raise serializers.ValidationError(
                "You have unpaid pending payments. Please complete them "
                "before creating a new borrowing."
            )

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            book = Book.objects.select_for_update().get(pk=validated_data["book"].pk)

            if book.inventory <= 0:
                raise serializers.ValidationError(
                    {"book": "This book is out of stock."}
                )

            book.inventory -= 1
            book.save()

            validated_data["book"] = book
            return Borrowing.objects.create(**validated_data)


class AdminBorrowingCreateSerializer(BorrowingCreateSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
    )

    class Meta(BorrowingCreateSerializer.Meta):
        fields = BorrowingCreateSerializer.Meta.fields + ("user",)
