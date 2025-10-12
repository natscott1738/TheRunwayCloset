# payments/views.py
import logging
from urllib.parse import urljoin

from rest_framework import views, status, permissions, viewsets
from rest_framework.response import Response
from django.urls import reverse
from django.conf import settings
from utils.permissions import PaymentPermission
from django.shortcuts import get_object_or_404

from .models import Payment
from .serializers import PaymentInitSerializer, PaymentReadSerializer
from orders.models import Order
from utils.daraja import stk_push
from utils.bank import create_bank_reference  # local helper

logger = logging.getLogger(__name__)


def build_daraja_callback(request):
    """
    Build a publicly reachable callback URL for Daraja.
    Uses DARAJA_CALLBACK_BASE from settings if set (e.g. an ngrok HTTPS URL).
    Falls back to request.build_absolute_uri(reverse(...)).
    """
    path = reverse("payments:mpesa_callback")  # e.g. /api/payments/mpesa/stk/callback/
    base = getattr(settings, "DARAJA_CALLBACK_BASE", None)
    if base:
        # Normalize base and join safely
        base = base.rstrip("/") + "/"
        return urljoin(base, path.lstrip("/"))
    return request.build_absolute_uri(path)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for Payments. Staff can see all, normal users only their payments.
    """
    queryset = Payment.objects.select_related("order")
    serializer_class = PaymentReadSerializer
    permission_classes = [PaymentPermission]

    def get_queryset(self):
        qs = Payment.objects.select_related("order", "order__user")
        user = self.request.user
        if user.is_staff or getattr(user, "role", None) in ["admin", "superadmin"]:
            return qs
        # customers → only their own
        return qs.filter(order__user=user)

class MPesaSTKInitiateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = PaymentInitSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)

        # ensure order exists and belongs to requester
        order = get_object_or_404(Order, pk=s.validated_data["order_id"], user=request.user)

        # Only allow mpesa method here (defensive)
        method = s.validated_data.get("method", "mpesa")
        if method != "mpesa":
            return Response({"detail": "Use bank init endpoint for bank_transfer method."},
                            status=status.HTTP_400_BAD_REQUEST)

        # build callback to be reachable by Daraja (ngrok or real domain)
        callback_url = build_daraja_callback(request)
        logger.debug("MPesa initiate: callback_url=%s order=%s user=%s", callback_url, order.id, request.user.id)

        # Ensure amount passed to provider is integer (Daraja expects integer KES)
        try:
            amount_int = int(float(order.total))
        except Exception:
            logger.exception("Invalid order total for order %s", order.id)
            return Response({"detail": "Invalid order total"}, status=status.HTTP_400_BAD_REQUEST)

        # call Daraja STK push and handle provider errors gracefully
        try:
            resp = stk_push(
                phone=s.validated_data["phone"],
                amount=amount_int,
                account_ref=str(order.id),
                callback_url=callback_url,
                description=f"Runway Order {order.id}",
            )
        except RuntimeError as exc:
            # provider returned a known error, include body if available
            logger.error("Daraja STK push failed for order %s: %s", order.id, exc)
            return Response({"detail": "Daraja STK push failed", "error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as exc:
            logger.exception("Unexpected error initiating Daraja STK for order %s: %s", order.id, exc)
            return Response({"detail": "Unexpected error initiating payment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # create or update local Payment record; method = mpesa
        p, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "amount": order.total,
                "currency": order.currency,
                "phone": s.validated_data.get("phone"),
                "status": Payment.Status.PENDING,
                "method": Payment.Method.MPESA,
            },
        )

        # update provider fields and status (persist changes)
        p.status = Payment.Status.PENDING
        # Daraja sandbox typically returns CheckoutRequestID
        p.provider_ref = resp.get("CheckoutRequestID") or resp.get("Response", {}).get("CheckoutRequestID") or p.provider_ref
        p.raw = resp
        p.save(update_fields=["status", "provider_ref", "raw", "updated_at"])

        serialized = PaymentReadSerializer(p, context={"request": request}).data
        return Response(serialized, status=status.HTTP_202_ACCEPTED)


class MPesaCallbackView(views.APIView):
    """
    Daraja will POST callback payloads here. Public endpoint.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        callback = data.get("Body", {}).get("stkCallback", {})
        checkout_id = callback.get("CheckoutRequestID")
        result_code = callback.get("ResultCode")

        p = Payment.objects.filter(provider_ref=checkout_id).first()
        if not p:
            logger.warning("MPesa callback: payment not found for checkout_id=%s", checkout_id)
            # Always respond 200 to Daraja quickly to avoid retries, but log for manual reconciliation
            return Response({"ok": True}, status=status.HTTP_200_OK)

        p.status = Payment.Status.SUCCESS if result_code == 0 else Payment.Status.FAILED
        p.raw = data
        p.save(update_fields=["status", "raw", "updated_at"])

        if p.status == Payment.Status.SUCCESS:
            # mark order as paid (idempotent)
            p.order.status = Order.Status.PAID
            p.order.save(update_fields=["status", "updated_at"])

        return Response({"ok": True}, status=status.HTTP_200_OK)


class BankInitiateView(views.APIView):
    """
    Initiate a bank transfer payment:
    - validates the request,
    - creates/reuses Payment record (method=bank_transfer),
    - calls create_bank_reference(payment) which persists provider_ref/raw/status.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        s = PaymentInitSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)

        order = get_object_or_404(Order, pk=s.validated_data["order_id"], user=request.user)

        # create or reuse Payment record for bank transfer
        p, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                "amount": order.total,
                "currency": order.currency,
                "phone": s.validated_data.get("phone", None),
                "status": Payment.Status.PENDING,
                "method": Payment.Method.BANK_TRANSFER,
            },
        )

        # Always (re)create a fresh bank reference/instructions.
        try:
            provider_resp = create_bank_reference(p)
        except Exception as exc:
            logger.exception("Failed to create bank reference for payment %s: %s", getattr(p, "id", None), exc)
            return Response({"detail": "Failed to generate bank reference"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serialized = PaymentReadSerializer(p, context={"request": request}).data
        return Response({"payment": serialized, "provider": provider_resp}, status=status.HTTP_201_CREATED)
