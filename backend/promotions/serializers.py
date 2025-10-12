# promotions/serializers.py
from rest_framework import serializers
from .models import Coupon, Promotion
from products.models import Product


class CouponSerializer(serializers.ModelSerializer):
    # expose computed property as read-only only
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "discount_percent",
            "start_date",
            "end_date",
            "is_active",    # computed only - single source of truth in API
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate_code(self, value: str) -> str:
        # normalize coupon codes to uppercase and strip whitespace
        return value.strip().upper()

    def validate_discount_percent(self, value: int) -> int:
        if value < 0 or value > 100:
            raise serializers.ValidationError("discount_percent must be between 0 and 100.")
        return value

    def validate(self, data):
        """
        Ensure end_date (if provided) is after start_date.
        When updating, check instance fallback so partial updates work.
        """
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        end = data.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date must be after start_date."})
        return data


class PromotionSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all(),
        required=False
    )
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = Promotion
        fields = [
            "id",
            "name",
            "products",
            "discount_percent",
            "start_date",
            "end_date",
            "is_active",    # only computed state is exposed
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_active", "created_at", "updated_at"]

    def validate_discount_percent(self, value: int) -> int:
        if value < 0 or value > 100:
            raise serializers.ValidationError("discount_percent must be between 0 and 100.")
        return value

    def validate(self, data):
        start = data.get("start_date", getattr(self.instance, "start_date", None))
        end = data.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "end_date must be after start_date."})
        return data

    def create(self, validated_data):
        products = validated_data.pop("products", [])
        promotion = super().create(validated_data)
        if products:
            promotion.products.set(products)
        return promotion

    def update(self, instance, validated_data):
        products = validated_data.pop("products", None)
        instance = super().update(instance, validated_data)
        if products is not None:
            instance.products.set(products)
        return instance
