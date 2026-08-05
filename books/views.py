from rest_framework import viewsets
from rest_framework_simplejwt.authentication import JWTAuthentication

from books.models import Book
from books.permissions import IsAdminOrReadOnly
from books.serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAdminOrReadOnly,)
