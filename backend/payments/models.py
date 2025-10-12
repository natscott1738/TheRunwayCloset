# payments/models.py (excerpt)
from django.db import models
import uuid
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel
from orders.models import Order
from utils.validators import validate_e164_phone

class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    class Currency(models.TextChoices):
        KES = "KES", "Kenyan Shilling"
        USD = "USD", "US Dollar"
        EUR = "EUR", "Euro"

    class Method(models.TextChoices):
        MPESA = "mpesa", "M-Pesa (mobile money)"
        BANK_TRANSFER = "bank_transfer", "Bank Transfer"
        # add other providers/methods here

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(
        Order, on_delete=models.PROTECT, related_name="payment"
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.KES, db_index=True)
    phone = models.CharField(max_length=20, validators=[validate_e164_phone], blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)

    # NEW: payment method (how the customer pays)
    method = models.CharField(max_length=32, choices=Method.choices, default=Method.MPESA, db_index=True)

    # provider_ref and raw are optional; backend populates them (read-only for clients)
    provider_ref = models.CharField(max_length=120, unique=True, blank=True, null=True, db_index=True)
    raw = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["currency"]),
            models.Index(fields=["method"]),
        ]

    def __str__(self):
        return f"Payment {self.id} ({self.method}) for Order {self.order_id} - {self.status}"
