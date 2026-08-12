from django.urls import reverse
from django.utils import timezone

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
    BorrowingCreateSerializer,
    AdminBorrowingCreateSerializer,
)
from borrowings.telegram_notifications import send_telegram_message
from payments.stripe_utils import create_stripe_session


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.select_related("book", "user")
    serializer_class = BorrowingSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return BorrowingListSerializer

        elif self.action == "retrieve":
            return BorrowingDetailSerializer

        elif self.action == "create":
            if self.request.user.is_staff:
                return AdminBorrowingCreateSerializer
            return BorrowingCreateSerializer

        return BorrowingSerializer

    def get_queryset(self):
        queryset = self.queryset

        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        is_active = self.request.query_params.get("is_active", None)

        if is_active is not None:
            if is_active.lower() == "true":
                queryset = queryset.filter(actual_return_date__isnull=True)
            elif is_active.lower() == "false":
                queryset = queryset.filter(actual_return_date__isnull=False)

        user_id = self.request.query_params.get("user_id", None)

        if user_id is not None and self.request.user.is_staff:
            queryset = queryset.filter(user_id=user_id)

        return queryset

    def perform_create(self, serializer):
        if self.request.user.is_staff and serializer.validated_data.get("user"):
            borrowing = serializer.save()
        else:
            borrowing = serializer.save(user=self.request.user)

        message = (
            f"📚 New borrowing created!\n"
            f"Book: {borrowing.book.title}\n"
            f"User: {borrowing.user.email}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )

        success_url = self.request.build_absolute_uri(
            reverse("payments:payment-success")
        )
        cancel_url = self.request.build_absolute_uri(
            reverse("payments:payment-cancel")
        )
        create_stripe_session(borrowing, success_url, cancel_url)

        send_telegram_message(message)

    @action(detail=True, methods=["POST"], url_path="return")
    def return_borrowing(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date is not None:
            return Response(
                {"detail": "This borrowing has already been returned."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        borrowing.actual_return_date = timezone.now().date()
        borrowing.save()

        book = borrowing.book
        book.inventory += 1
        book.save()

        return Response(
            {"detail": "Borrowing successfully returned."},
            status=status.HTTP_200_OK,
        )
