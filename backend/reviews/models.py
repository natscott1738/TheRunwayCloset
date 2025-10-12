import uuid
from django.db import models
from django.conf import settings
from django.db.models import Q, CheckConstraint

from core.models import TimeStampedModel
from products.models import Product


class Review(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True
    )
    rating = models.PositiveSmallIntegerField()  # will be enforced 1–5 by constraint
    comment = models.TextField(blank=True)

    class Meta:
        constraints = [
            # enforce rating between 1 and 5
            CheckConstraint(
                check=Q(rating__gte=1) & Q(rating__lte=5),
                name="rating_between_1_and_5"
            ),
            # enforce one review per user per product
            models.UniqueConstraint(
                fields=['user', 'product'],
                name="unique_user_product_review"
            ),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.rating}★ by {self.user} on {self.product}"
