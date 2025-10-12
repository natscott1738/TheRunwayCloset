# orders/views.py
from rest_framework import viewsets, permissions
from utils.permissions import OrderPermission
from .models import Order
from .serializers import OrderSerializer


class OrderViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "put", "patch", "delete"]
    serializer_class = OrderSerializer
    permission_classes = [OrderPermission]

    def get_queryset(self):
        """
        Staff/admin: can see all orders.
        Seller: can list all orders (read-only handled by permission).
        Customer: only their own orders.
        """
        qs = Order.objects.prefetch_related('items__product')
        user = self.request.user
        if user is None or not getattr(user, "is_authenticated", False):
            return qs.none()
        if user.is_staff or getattr(user, "role", None) in ("admin", "superadmin"):
            return qs
        if getattr(user, "role", None) == "seller":
            # seller reads all orders (they may filter in UI)
            return qs
        # customer
        return qs.filter(user=user)

    def perform_create(self, serializer):
        """
        Ensure the order is always linked to the authenticated user
        and default currency is respected.
        """
        serializer.save(
            user=self.request.user,
            currency=serializer.validated_data.get("currency", "KES")  # default enforced
        )
