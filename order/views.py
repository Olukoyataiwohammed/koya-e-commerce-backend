from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
import requests
import uuid
import hashlib
import hmac
import json

from decimal import Decimal

from .serializers import OrderSerializer
from .models import Order, OrderItem, Payment
from accounts.models import Address
from store.models import Product   # ✅ IMPORTANT


# -----------------------------------------
# CREATE ORDER (FIXED)
# -----------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    data = request.data.copy()
    items_data = data.pop("items", [])

    # ✅ Validate items
    if not items_data:
        return Response({"error": "No items provided"}, status=400)

    # -----------------------------
    # Handle address
    # -----------------------------
    if "address_id" in data:
        try:
            address = Address.objects.get(id=data["address_id"])
        except Address.DoesNotExist:
            return Response({"error": "Address not found"}, status=400)
    else:
        address = Address.objects.create(
            full_name=data.get("full_name", ""),
            phone=data.get("phone", ""),
            address=data.get("address", ""),
            city=data.get("city", ""),
            state=data.get("state", ""),
            country=data.get("country", ""),
            postal_code=data.get("postal_code", ""),
        )

    # -----------------------------
    # Calculate totals (SECURE)
    # -----------------------------
    subtotal = Decimal("0.00")
    order_items = []

    for item in items_data:
        try:
            product = Product.objects.get(id=item["product"])
        except Product.DoesNotExist:
            return Response({"error": f"Product {item['product']} not found"}, status=400)

        quantity = int(item.get("quantity", 1))

        subtotal += product.price * quantity

        order_items.append({
            "product": product,
            "quantity": quantity,
            "price": product.price  # ✅ snapshot price
        })

    shipping_fee = Decimal(data.get("shipping_fee", 0))
    total = subtotal + shipping_fee

    # -----------------------------
    # Create order
    # -----------------------------
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key,
        address=address,
        payment_method=data.get("payment_method", "card").lower(),
        full_name=data.get("full_name", ""),
        phone=data.get("phone", ""),
        subtotal=subtotal,
        shipping_fee=shipping_fee,
        total=total
    )

    # -----------------------------
    # Create order items (FIXED)
    # -----------------------------
    for item in order_items:
        OrderItem.objects.create(
            order=order,
            product=item["product"],
            price=item["price"],
            quantity=item["quantity"]
        )

    # -----------------------------
    # Response
    # -----------------------------
    serializer = OrderSerializer(order, context={'request': request})
    return Response({"order": serializer.data}, status=status.HTTP_201_CREATED)


# -----------------------------------------
# LIST USER ORDERS
# -----------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True, context={'request': request})
    return Response(serializer.data)


# -----------------------------------------
# ORDER DETAIL
# -----------------------------------------
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    try:
        order = Order.objects.get(pk=pk, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    serializer = OrderSerializer(order, context={'request': request})
    return Response(serializer.data)


# -----------------------------------------
# CREATE PAYMENT
# -----------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    order_id = request.data.get("order")

    if not order_id:
        return Response({"error": "Order ID is required"}, status=400)

    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    if order.is_paid:
        return Response({"error": "Order already paid"}, status=400)

    if Payment.objects.filter(order=order, status="PENDING").exists():
        return Response({"error": "Payment already initialized"}, status=400)

    reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        order=order,
        amount=order.total,
        method="CARD",
        transaction_id=reference,
        status="PENDING"
    )

    return Response({
        "reference": reference,
        "amount": int(payment.amount * 100),
        "email": request.user.email
    }, status=201)


# -----------------------------------------
# VERIFY PAYMENT
# -----------------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    reference = request.data.get("reference")

    if not reference:
        return Response({"error": "Reference required"}, status=400)

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
    except Exception:
        return Response({"error": "Paystack connection failed"}, status=500)

    if not data.get("status"):
        return Response({"error": "Verification failed"}, status=400)

    payment_data = data.get("data")

    if payment_data.get("status") != "success":
        return Response({"error": "Payment not successful"}, status=400)

    try:
        payment = Payment.objects.get(transaction_id=reference)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=404)

    order = payment.order

    if payment.status == "COMPLETED":
        return Response({"message": "Already verified"})

    amount = payment_data.get("amount") / 100

    if float(amount) != float(order.total):
        return Response({"error": "Amount mismatch"}, status=400)

    payment.status = "COMPLETED"
    payment.save()

    order.is_paid = True
    order.status = "PROCESSING"
    order.save()

    return Response({"message": "Payment verified successfully"})


# -----------------------------------------
# PAYSTACK WEBHOOK
# -----------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request):
    payload = request.body
    signature = request.headers.get('x-paystack-signature')

    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode('utf-8'),
        payload,
        hashlib.sha512
    ).hexdigest()

    if computed_signature != signature:
        return Response({"error": "Invalid signature"}, status=400)

    data = json.loads(payload)

    if data.get("event") != "charge.success":
        return Response({"message": "Event ignored"}, status=200)

    payment_data = data.get("data")

    reference = payment_data.get("reference")
    amount = payment_data.get("amount") / 100

    try:
        payment = Payment.objects.get(transaction_id=reference)
    except Payment.DoesNotExist:
        return Response({"error": "Payment not found"}, status=404)

    order = payment.order

    if payment.status == "COMPLETED":
        return Response({"message": "Already processed"}, status=200)

    if float(amount) != float(order.total):
        return Response({"error": "Amount mismatch"}, status=400)

    payment.status = "COMPLETED"
    payment.save()

    order.is_paid = True
    order.status = "PROCESSING"
    order.save()

    return Response({"message": "Webhook processed successfully"})