from decimal import Decimal
import logging
from rest_framework import serializers
from django.core.exceptions import ValidationError
from .models import Payment
from orders.models import Order
from utils.validators import validate_e164_phone

logger = logging.getLogger(__name__)

class PaymentInitSerializer(serializers.Serializer):
    """
    Client payload for initiating payments.
    - order_id: UUID of an existing Order
    - method: 'mpesa' or 'bank_transfer'
    - phone: required for mpesa, optional for bank_transfer
    """
    order_id = serializers.UUIDField()
    method = serializers.ChoiceField(choices=[("mpesa", "mpesa"), ("bank_transfer", "bank_transfer")], default="mpesa")
    phone = serializers.CharField(max_length=20, required=False, allow_null=True, allow_blank=True)

    def validate_order_id(self, value):
        try:
            order = Order.objects.get(pk=value)
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found.")
        # ensure order is in pending state
        if order.status != Order.Status.PENDING:
            raise serializers.ValidationError("Only pending orders can be paid.")
        # ensure order has no existing payment (OneToOne)
        if hasattr(order, "payment"):
            raise serializers.ValidationError("This order already has a payment.")
        return value

    def validate(self, attrs):
        # permission check: ensure the requester is owner or staff
        request = self.context.get("request", None)
        order = Order.objects.get(pk=attrs['order_id'])
        if request is not None and not (request.user.is_staff or order.user == request.user):
            raise serializers.ValidationError("You do not have permission to initiate payment for this order.")

        method = attrs.get("method", "mpesa")
        phone = attrs.get("phone")

        # mpesa requires a valid phone in E.164
        if method == "mpesa":
            if not phone:
                raise serializers.ValidationError({"phone": "Phone number is required for M-Pesa payments."})
            # validate format (will raise if invalid)
            try:
                validate_e164_phone(phone)
            except Exception as exc:
                raise serializers.ValidationError({"phone": "Phone number must be in E.164 format (e.g. +2547...)."})
        # bank_transfer does NOT require phone; if provided, we still validate format
        elif method == "bank_transfer" and phone:
            try:
                validate_e164_phone(phone)
            except Exception:
                raise serializers.ValidationError({"phone": "Phone number must be in E.164 format (e.g. +2547...)."})
        return attrs
    

class PaymentReadSerializer(serializers.ModelSerializer):
    """
    Returns full payment info including provider_ref and raw, but these are read-only.
    Masks phone for non-staff users for privacy.
    """
    phone = serializers.CharField()
    provider_ref = serializers.CharField(read_only=True)
    raw = serializers.JSONField(read_only=True)

    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'amount', 'currency', 'phone',
            'status', 'provider_ref', 'raw',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order', 'amount', 'currency', 'status',
            'provider_ref', 'raw', 'created_at', 'updated_at'
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request', None)
        if request is None or not getattr(request.user, "is_staff", False):
            phone = data.get('phone')
            if phone:
                masked = f"{'*' * max(0, len(phone) - 4)}{phone[-4:]}"
                data['phone'] = masked
        return data