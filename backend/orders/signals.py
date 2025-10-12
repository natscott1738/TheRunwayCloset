from decimal import Decimal
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from .models import OrderItem, Order


@receiver(pre_save, sender=OrderItem)
def ensure_unit_price(sender, instance: OrderItem, **kwargs):
    """
    Ensure unit_price is set from the product if not provided.
    """
    if instance.product and (instance.unit_price is None):
        # assume Product has a `price` field
        instance.unit_price = instance.product.price


def _recalculate_order_total(order: Order):
    """
    Recalculate and save the total for the given order from its items.
    """
    if order is None:
        return

    expr = ExpressionWrapper(F('unit_price') * F('quantity'), output_field=DecimalField())
    agg = order.items.aggregate(total=Sum(expr))
    total = agg['total'] or Decimal('0.00')

    # Only save if changed (optional optimization)
    if order.total != total:
        order.total = total
        order.save(update_fields=['total'])


@receiver(post_save, sender=OrderItem)
def orderitem_post_save(sender, instance: OrderItem, **kwargs):
    """
    After an OrderItem is created/updated, recalc the parent order total.
    """
    _recalculate_order_total(instance.order)


@receiver(post_delete, sender=OrderItem)
def orderitem_post_delete(sender, instance: OrderItem, **kwargs):
    """
    After an OrderItem is deleted, recalc the parent order total.
    """
    # instance.order may be None after delete in some DB backends; fetch by id if needed.
    order = instance.order
    if order is not None:
        _recalculate_order_total(order)
