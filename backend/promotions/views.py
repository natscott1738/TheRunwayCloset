from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Coupon, Promotion
from .serializers import CouponSerializer, PromotionSerializer
from utils.permissions import IsSellerOrAdminOrReadOnly


class CouponViewSet(viewsets.ModelViewSet):
    """
    Admins can CRUD coupons; others read-only.
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsSellerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["code"]
    ordering_fields = ["created_at", "updated_at", "discount_percent"]
    ordering = ["-created_at"]


class PromotionViewSet(viewsets.ModelViewSet):
    """
    Admins can CRUD promotions; others read-only.
    """
    queryset = Promotion.objects.prefetch_related("products").all()
    serializer_class = PromotionSerializer
    permission_classes = [IsSellerOrAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["created_at", "updated_at", "discount_percent"]
    ordering = ["-created_at"]
