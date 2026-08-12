from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from payments.models import Payment
from payments.serializers import PaymentListSerializer, PaymentDetailSerializer


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Payment.objects.select_related(
        "borrowing", "borrowing__book", "borrowing__user"
    )
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "list":
            return PaymentListSerializer
        return PaymentDetailSerializer

    def get_queryset(self):
        queryset = self.queryset

        if not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)

        return queryset

    @action(detail=False, methods=["GET"], url_path="success")
    def success(self, request):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response(
                {"detail": "session_id query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            payment = Payment.objects.get(session_id=session_id)
        except Payment.DoesNotExist:
            return Response(
                {"detail": "Payment not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if payment.status == Payment.StatusChoices.PAID:
            return Response(
                {"detail": "Payment was already confirmed."},
                status=status.HTTP_200_OK,
            )

        payment.status = Payment.StatusChoices.PAID
        payment.save()

        return Response(
            {"detail": "Payment successful. Thank you!"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["GET"], url_path="cancel")
    def cancel(self, request):
        session_id = request.query_params.get("session_id")

        response_data = {
            "detail": (
                "Payment was not completed. Your Stripe session is still "
                "valid for 24 hours — you can complete the payment using "
                "the link below."
            )
        }

        if session_id:
            payment = Payment.objects.filter(session_id=session_id).first()
            if payment:
                response_data["session_url"] = payment.session_url

        return Response(response_data, status=status.HTTP_200_OK)
