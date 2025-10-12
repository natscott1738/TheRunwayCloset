import uuid
from django.db import models
from core.models import TimeStampedModel
from products.models import Product

class Warehouse(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    location = models.CharField(max_length=255, blank=True)
    def __str__(self): return self.name

class StockItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_items')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_items')
    quantity = models.PositiveIntegerField(default=0)
    class Meta:
        unique_together = ('product','warehouse')
