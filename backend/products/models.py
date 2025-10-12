import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel
from utils.validators import unique_slugify


class Category(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(unique=True, max_length=60, blank=True, db_index=True)

    class Meta:
        ordering = ['name']  # alphabetical for categories

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,# adjust if using created_at/updated_at
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='products'
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=80, blank=True, db_index=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='KES',
        db_index=True
    )
    is_published = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-created_at']  # newest first

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ProductImage(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/')
    alt = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['id']  # stable ordering for image sets
