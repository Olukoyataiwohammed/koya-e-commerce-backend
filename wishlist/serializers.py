from rest_framework import serializers
from wishlist.models import Wishlist
from store.models import Product


class WishlistSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True
    )

    product = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            "id",
            "product_id",
            "product",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_product(self, obj):
        product = obj.product
        return {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "image": product.image.url if product.image else None,
        }
