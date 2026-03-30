from rest_framework import serializers
from .models import Order, OrderItem
from accounts.models import Address
from cart.models import Cart, CartItem


# -----------------------------------------
# Address Serializer
# -----------------------------------------
class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "address"]


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

    address = AddressSerializer(read_only=True)

    address_id = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        source='address',
        write_only=True,
        required=False
    )

    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_CHOICES)
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

    # ✅ FIX TOTAL (includes shipping)
    def get_total(self, obj):
        return obj.subtotal + obj.shipping_fee


    # -----------------------------------------
    # CREATE ORDER (WITH CART ITEMS)
    # -----------------------------------------
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        address = validated_data.pop('address', None)

        # Assign user
        if user and user.is_authenticated:
            validated_data['user'] = user
            cart = Cart.objects.filter(user=user).first()
        else:
            session_key = request.session.session_key
            validated_data['session_key'] = session_key
            cart = Cart.objects.filter(session_key=session_key).first()

        validated_data['address'] = address

        order = Order.objects.create(**validated_data)

        # ✅ MOVE CART ITEMS → ORDER ITEMS
        subtotal = 0

        if cart:
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
                subtotal += item.product.price * item.quantity

            # ✅ clear cart after order
            cart.items.all().delete()

        # ✅ SAVE SUBTOTAL
        order.subtotal = subtotal
        order.save()

        return order