from django.shortcuts import render

# Create your views here.


from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, LoginSerializer,  AddressSerializer
from cart.utils import merge_guest_cart_to_user
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Address

@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # Optionally return token on register
        refresh = RefreshToken.for_user(user)
        return Response({
            "message": "User registered successfully",
            "user_id": user.id,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_user(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']

    # 🔹 Ensure guest session exists
    if not request.session.session_key:
        request.session.create()

    # 🔹 Save guest session key
    guest_session_key = request.session.session_key

    # 🔹 Merge guest cart into user cart
    merge_guest_cart_to_user(user, guest_session_key)

    # 🔹 Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        "user_id": user.id,
        "access": str(refresh.access_token),
        "refresh": str(refresh)
    }, status=status.HTTP_200_OK)





@api_view(["POST"])
def logout_user(request):
    """
    Blacklist refresh token (JWT) and clear session.
    Expects: { "refresh": "<refresh_token>" }
    """
    try:
        # 🔹 Blacklist JWT token
        refresh_token = request.data.get("refresh")
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()

        # 🔹 Clear session completely to reset guest cart
        request.session.flush()  # creates a new session automatically

        return Response({"message": "Logged out successfully"}, status=205)
    except Exception:
        return Response({"error": "Invalid token"}, status=400)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def list_addresses(request):
    addresses = Address.objects.filter(user=request.user)
    serializer = AddressSerializer(addresses, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def create_address(request):
    serializer = AddressSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)