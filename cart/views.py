from django.shortcuts import render

# Create your views here.

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from store.models import Product
from .models import CartItem
from .serializers import CartSerializer
from .utils import get_or_create_cart



@api_view(["GET"])
@permission_classes([AllowAny])
def cart_detail(request):
    cart = get_or_create_cart(request)
    serializer = CartSerializer(cart)
    return Response(serializer.data)



@api_view(["POST"])
@permission_classes([AllowAny])
def add_to_cart(request):
    cart = get_or_create_cart(request)

    product_id = request.data.get("product_id")
    quantity = int(request.data.get("quantity", 1))

    if not product_id:
        return Response(
            {"error": "product_id is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        product = Product.objects.get(id=product_id, is_available=True)
    except Product.DoesNotExist:
        return Response(
            {"error": "Product not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created:
        cart_item.quantity += quantity
    else:
        cart_item.quantity = quantity

    cart_item.save()

    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PUT"])
@permission_classes([AllowAny])
def update_cart_item(request, item_id):
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    quantity = int(request.data.get("quantity", 1))

    if quantity < 1:
        cart_item.delete()
    else:
        cart_item.quantity = quantity
        cart_item.save()

    serializer = CartSerializer(cart)
    return Response(serializer.data)

@api_view(["DELETE"])
@permission_classes([AllowAny])
def decrease_product_from_cart(request, item_id):
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # Reduce quantity instead of deleting immediately --->
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    serializer = CartSerializer(cart)
    return Response(serializer.data)



@api_view(["DELETE"])
@permission_classes([AllowAny])
def remove_from_cart(request, item_id):
    cart = get_or_create_cart(request)

    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    cart_item.delete()

    serializer = CartSerializer(cart)
    return Response(serializer.data)


@api_view(["DELETE"])
@permission_classes([AllowAny])
def clear_cart(request):
    cart = get_or_create_cart(request)
    cart.items.all().delete()

    serializer = CartSerializer(cart)
    return Response(serializer.data)
