# utils/providers/bank.py
import uuid
import logging
from typing import Dict, Any
from django.conf import settings
from django.db import IntegrityError, transaction

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def _generate_ref(order_id) -> str:
    order_part = str(order_id).replace("-", "")[:8]
    rand_part = uuid.uuid4().hex[:6]
    return f"RUNWAY-{order_part}-{rand_part}"


def create_bank_reference(payment) -> Dict[str, Any]:
    """
    Generate and persist a unique bank transfer reference for a Payment instance.

    Mutates and saves the given `payment` object.

    Expects BANK_NAME, BANK_ACCOUNT_NAME, BANK_ACCOUNT_NUMBER to be present in settings.
    """
    if not hasattr(payment, "order_id"):
        raise ValueError("Expected a Payment instance with an order_id attribute")

    # ensure required settings exist
    try:
        instructions_template = {
            "bank_name": settings.BANK_NAME,
            "account_name": settings.BANK_ACCOUNT_NAME,
            "account_number": settings.BANK_ACCOUNT_NUMBER,
        }
    except AttributeError as exc:
        raise RuntimeError("Bank configuration missing in settings") from exc

    for attempt in range(1, MAX_ATTEMPTS + 1):
        ref = _generate_ref(payment.order_id)
        instructions = {
            **instructions_template,
            "reference": ref,
            "notes": f"Please include reference {ref} when making the bank transfer."
        }

        payment.provider_ref = ref
        payment.raw = {"instructions": instructions}
        payment.status = (
            payment.__class__.Status.PENDING
            if hasattr(payment.__class__, "Status") and hasattr(payment.__class__.Status, "PENDING")
            else "pending"
        )

        try:
            with transaction.atomic():
                payment.save(update_fields=["provider_ref", "raw", "status"])
            logger.info(
                "Created bank reference %s for payment %s (order %s)", ref, getattr(payment, "id", None), getattr(payment, "order_id", None)
            )
            return {"reference": ref, "instructions": instructions}
        except IntegrityError as exc:
            logger.warning("Bank reference collision on attempt %d for %s: %s", attempt, ref, exc)
            # try again with a new ref
            continue

    # exhausted attempts
    logger.error("Could not generate a unique bank reference after %d attempts for payment %s", MAX_ATTEMPTS, getattr(payment, "id", None))
    raise RuntimeError("Could not generate a unique bank reference after multiple attempts")
