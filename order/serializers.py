from rest_framework import serializers
from .models import Order, OrderItem
from accounts.models import Address


# -----------------------------------------
# Address Serializer (FIXES address showing "4")
# -----------------------------------------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "address"]  # adjust if you use street/city/etc


# -----------------------------------------
# Order Item Serializer
# -----------------------------------------
class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_image',
            'price',
            'quantity',
            'total'
        ]
        read_only_fields = ['id', 'product_name', 'product_image', 'total']

    def get_total(self, obj):
        return obj.price * obj.quantity


# -----------------------------------------
# Main Order Serializer
# -----------------------------------------
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    #  Show full address instead of ID
    address = AddressSerializer(read_only=True)

    #  Accept address_id from frontend
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='address',
        write_only=True,
        required=False
    )

    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_CHOICES)

    #  FIX total calculation
    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'user',
            'session_key',
            'full_name',
            'phone',
            'address',
            'address_id',
            'payment_method',
            'status',
            'subtotal',
            'shipping_fee',
            'total',
            'is_paid',
            'payment_reference',
            'items',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'user',
            'session_key',
            'status',
            'subtotal',
            'total',
            'is_paid',
            'payment_reference',
            'items',
            'created_at',
            'updated_at'
        ]

    # -----------------------------------------
    # ✅ FIX TOTAL (THIS FIXES ₦0.00)
    # -----------------------------------------
    def get_total(self, obj):
        return sum(item.price * item.quantity for item in obj.items.all())


    # -----------------------------------------
    # CREATE ORDER
    # -----------------------------------------
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        #  extract address
        address = validated_data.pop('address', None)

        # If frontend sent new address object
        if isinstance(address, dict):
            address = Address.objects.create(user=user, **address)

        # Assign user
        if user and user.is_authenticated:
            validated_data['user'] = user

        # Assign address properly
        validated_data['address'] = address

       
        order = Order.objects.create(**validated_data)

        return order