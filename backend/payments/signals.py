import logging
from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment
from orders.models import Order

# import the notification service (make sure notifications app is installed)
try:
    from notifications.services import create_and_dispatch_notification
except Exception:
    create_and_dispatch_notification = None

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def handle_payment_status_change(sender, instance: Payment, created, **kwargs):
    """
    When a payment becomes SUCCESS, update the related Order to 'paid'
    only if the payment currency matches the order currency and amounts match.
    Also dispatch notifications to the buyer and the seller(s).
    """
    try:
        # only act when payment is in success state
        if instance.status != Payment.Status.SUCCESS:
            return

        order = getattr(instance, "order", None)
        if order is None:
            logger.warning("Payment %s has no related order; skipping.", getattr(instance, "pk", None))
            return

        # If order already marked paid/fulfilled, nothing to do
        if order.status == Order.Status.PAID:
            logger.debug("Order %s already paid; no action.", order.pk)
            return

        # Ensure currency matches between payment and order
        if instance.currency != order.currency:
            logger.warning(
                "Payment currency %s does not match order currency %s for order %s. Manual reconciliation required.",
                instance.currency, order.currency, order.pk
            )
            return

        # Compare amounts conservatively using Decimal
        try:
            payment_amount = Decimal(instance.amount)
            order_total = Decimal(order.total)
        except Exception:
            logger.exception("Could not parse amounts for payment %s and order %s", getattr(instance, "pk", None), getattr(order, "pk", None))
            return

        if payment_amount == order_total:
            # Idempotent update
            order.status = Order.Status.PAID
            order.save(update_fields=['status', 'updated_at'])
            logger.info(
                "Order %s marked as PAID due to successful payment %s", order.pk, instance.pk
            )

            # Notify buyer
            try:
                if create_and_dispatch_notification:
                    create_and_dispatch_notification(
                        user=order.user,
                        title="Payment received",
                        body=f"Payment for order {order.id} of amount {instance.amount} {instance.currency} succeeded.",
                        data={"order_id": str(order.id), "payment_id": str(instance.id)},
                        channels=["in_app", "email"],
                        notif_type="payment",
                    )
                else:
                    logger.debug("create_and_dispatch_notification not available; skipping buyer notification.")
            except Exception:
                logger.exception("Failed to create/dispatch notification for buyer on order %s", order.pk)

            # Notify seller(s) per order item (defensive)
            try:
                # If your OrderItem relation is named 'items' (adjust if different)
                for item in order.items.select_related("product__seller").all():
                    seller = getattr(item.product, "seller", None)
                    if seller:
                        try:
                            if create_and_dispatch_notification:
                                create_and_dispatch_notification(
                                    user=seller,
                                    title="Order paid",
                                    body=f"Order {order.id} for {item.quantity} x {item.product.title} has been paid.",
                                    data={"order_id": str(order.id), "product_id": str(item.product.id)},
                                    channels=["in_app", "email"],
                                    notif_type="order",
                                )
                        except Exception:
                            logger.exception("Failed to notify seller %s for order %s", getattr(seller, "pk", None), order.pk)
            except Exception:
                logger.exception("Error iterating order items for order %s while notifying sellers", order.pk)

        else:
            # amounts mismatch — log a warning for manual review
            logger.warning(
                "Payment/Order amount mismatch: payment=%s order=%s (payment_id=%s). Manual reconciliation required.",
                payment_amount, order_total, instance.pk
            )

    except Exception as exc:
        logger.exception(
            "Error in payment post_save handler for payment %s: %s",
            getattr(instance, 'pk', None), exc
        )
