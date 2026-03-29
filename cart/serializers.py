from rest_framework import serializers
from .models import Cart, CartItem
from store.models import Product


# 🔹 Product serializer (minimal, for cart display)
class CartProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "price",
            "image",
            "slug",
        ]


# 🔹 Cart item serializer
class CartItemSerializer(serializers.ModelSerializer):
    product = CartProductSerializer(read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "quantity",
            "total_price",
        ]

    def get_total_price(self, obj):
        return obj.quantity * obj.product.price


# 🔹 Cart serializer
class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            "id",
            "items",
            "cart_total",
            "created_at",
        ]

    def get_cart_total(self, obj):
        return sum(item.quantity * float(item.product.price) for item in obj.items.all())

