from django.contrib.auth import get_user_model
from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing
from users.serializers import UserSerializer


class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingListSerializer(BorrowingSerializer):
    book = BookSerializer(read_only=True)
    user = serializers.SlugRelatedField(read_only=True, slug_field="email")


class BorrowingDetailSerializer(BorrowingListSerializer):
    user = UserSerializer(read_only=True)


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("book", "expected_return_date")

    @staticmethod
    def validate_book(self, value):
        if value.inventory <= 0:
            raise serializers.ValidationError("This book is out of stock.")
        return value


class AdminBorrowingCreateSerializer(BorrowingCreateSerializer):
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
    )

    class Meta(BorrowingCreateSerializer.Meta):
        fields = BorrowingCreateSerializer.Meta.fields + ("user",)
