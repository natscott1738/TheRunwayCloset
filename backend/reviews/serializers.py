from django.db import IntegrityError
from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    # user is readonly and injected from request.user in create()
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    # explicit bounds on rating (1..5)
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = ["id", "user", "product", "rating", "comment", "created_at"]
        read_only_fields = ["id", "user", "created_at"]

    def validate(self, attrs):
        """
        Ensure the request is authenticated and the user hasn't already reviewed the product.
        Doing this here yields a clear validation error instead of a DB IntegrityError.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create a review.")

        # product must be present for creation; for update it may not be in attrs
        product = attrs.get("product")
        # Only check uniqueness on create (or when product is explicitly changed)
        if self.instance is None and product is not None:
            if Review.objects.filter(user=user, product=product).exists():
                raise serializers.ValidationError("You have already reviewed this product.")

        # If attempting to change product on update, forbid it
        if self.instance is not None and "product" in attrs:
            if attrs["product"] != self.instance.product:
                raise serializers.ValidationError("Changing the product of a review is not allowed.")

        return attrs

    def create(self, validated_data):
        """
        Inject request.user as the review owner and handle racing UniqueConstraint errors gracefully.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated:
            raise serializers.ValidationError("Authentication required to create a review.")

        validated_data["user"] = user
        try:
            return super().create(validated_data)
        except IntegrityError:
            # In case of a race condition where another review was created concurrently
            raise serializers.ValidationError("You have already reviewed this product.")

    def update(self, instance, validated_data):
        # Prevent changing the review owner (just in case) and product
        validated_data.pop("user", None)
        if "product" in validated_data and validated_data["product"] != instance.product:
            raise serializers.ValidationError("Changing the product of a review is not allowed.")
        return super().update(instance, validated_data)
