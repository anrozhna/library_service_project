from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from borrowings.models import Borrowing
from borrowings.serializers import (
    BorrowingSerializer,
    BorrowingListSerializer,
    BorrowingDetailSerializer,
)


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all().select_related("book", "user")
    serializer_class = BorrowingSerializer
    authentication_classes = (JWTAuthentication,)

    def get_serializer_class(self):
        serializer = self.serializer_class
        if self.action == "list":
            serializer = BorrowingListSerializer
        elif self.action == "retrieve":
            serializer = BorrowingDetailSerializer
        return serializer

    def get_queryset(self):
        queryset = self.queryset

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(user=self.request.user)
