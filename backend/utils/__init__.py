# utils/providers/__init__.py
"""
Unified provider interface for all payment methods.
Import this to get a callable function for a specific payment method.
"""

def get_provider(method):
    """
    Returns a callable for the payment method.
    method: str -> "mpesa", "stripe", "paypal", "bank_transfer"
    """
    if method == "mpesa":
        from .daraja import stk_push
        return stk_push
    elif method == "bank_transfer":
        from .bank import create_bank_reference
        return create_bank_reference
    return None
