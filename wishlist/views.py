from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from wishlist.models import Wishlist
from wishlist.serializers import WishlistSerializer
from store.models import Product


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wishlist_list(request):
    """
    Get all wishlist items for logged-in user
    """
    wishlist_items = Wishlist.objects.filter(user=request.user)
    serializer = WishlistSerializer(wishlist_items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    """
    Add a product to wishlist
    Expects: { "product_id": <int> }
    """
    serializer = WishlistSerializer(data=request.data)

    if serializer.is_valid():
        product = serializer.validated_data["product"]

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            return Response(
                {"detail": "Product already in wishlist"},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            WishlistSerializer(wishlist_item).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, product_id):
    """
    Remove product from wishlist
    """
    try:
        wishlist_item = Wishlist.objects.get(
            user=request.user,
            product_id=product_id
        )
        wishlist_item.delete()
        return Response(
            {"detail": "Removed from wishlist"},
            status=status.HTTP_204_NO_CONTENT
        )
    except Wishlist.DoesNotExist:
        return Response(
            {"detail": "Product not found in wishlist"},
            status=status.HTTP_404_NOT_FOUND
        )







