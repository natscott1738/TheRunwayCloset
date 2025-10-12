from rest_framework import serializers
from .models import Order, OrderItem
from products.models import Product


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_published=True),
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    currency = serializers.ChoiceField(
        choices=[("USD", "USD"), ("KES", "KES"), ("EUR", "EUR")],
        default="KES"
    )
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'status', 'currency', 'total', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'total']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)

        for item in items_data:
            product = item['product']
            quantity = item['quantity']
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price  # set unit price here; signals will recalc total
            )

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update order-level fields
        for attr in ['status', 'currency']:
            if attr in validated_data:
                setattr(instance, attr, validated_data[attr])
        instance.save()

        if items_data is not None:
            # Partial update semantics: update existing, add new, remove missing
            existing_items = {item.product.id: item for item in instance.items.all()}
            payload_product_ids = []

            for item in items_data:
                product = item['product']
                quantity = item['quantity']
                payload_product_ids.append(product.id)

                if product.id in existing_items:
                    order_item = existing_items[product.id]
                    order_item.quantity = quantity
                    order_item.unit_price = product.price
                    order_item.save()
                else:
                    OrderItem.objects.create(
                        order=instance,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price
                    )

            # Remove items not present in payload
            instance.items.exclude(product_id__in=payload_product_ids).delete()

            # No need to recalc total here — signals will handle it

        return instance
