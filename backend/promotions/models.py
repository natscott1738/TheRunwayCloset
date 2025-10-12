import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, CheckConstraint

from core.models import TimeStampedModel
from products.models import Product


class Coupon(TimeStampedModel):
    """
    Coupon applied at checkout. Validity determined by `active` flag
    and optional `start_date` / `end_date`.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True, db_index=True)
    discount_percent = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage (0-100)."
    )
    active = models.BooleanField(default=True, db_index=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            CheckConstraint(
                check=Q(discount_percent__gte=0) & Q(discount_percent__lte=100),
                name="coupon_discount_between_0_and_100",
            ),
        ]

    def __str__(self):
        return self.code

    @property
    def active(self) -> bool:
        """
        True if coupon is flagged active and (if provided) current time is within start/end window.
        """
        now = timezone.now()
        if not self.active:
            return False
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class Promotion(TimeStampedModel):
    """
    Promotion that can be applied to one or more products. Has same validity semantics
    as Coupon (active flag + optional start/end dates).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    products = models.ManyToManyField(Product, related_name="promotions", blank=True)
    discount_percent = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Discount percentage applied to listed products (0-100)."
    )
    active = models.BooleanField(default=True, db_index=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            CheckConstraint(
                check=Q(discount_percent__gte=0) & Q(discount_percent__lte=100),
                name="promotion_discount_between_0_and_100",
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def active(self) -> bool:
        """
        True if promotion is flagged active and (if provided) current time is within start/end window.
        """
        now = timezone.now()
        if not self.active:
            return False
        if self.start_date and self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True
