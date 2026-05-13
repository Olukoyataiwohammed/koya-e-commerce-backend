from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from django.db import transaction

import requests
import uuid
import hashlib
import hmac
import json

from decimal import Decimal, InvalidOperation

from .serializers import OrderSerializer
from .models import Order, OrderItem, Payment
from accounts.models import Address
from store.models import Product


# =========================================
# CREATE ORDER
# =========================================
@api_view(["POST"])
@permission_classes([AllowAny])
def create_order(request):
    data = request.data.copy()
    items_data = data.get("items", [])

    # -----------------------------
    # Validate items
    # -----------------------------
    if not items_data:
        return Response(
            {"error": "No items provided"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():

            # -----------------------------
            # Handle Address
            # -----------------------------
            address_id = data.get("address_id")

            if address_id:
                try:
                    address = Address.objects.get(id=address_id)
                except Address.DoesNotExist:
                    return Response(
                        {"error": "Address not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                address = Address.objects.create(
                    full_name=data.get("full_name", "").strip(),
                    phone=data.get("phone", "").strip(),
                    address=data.get("address", "").strip(),
                    city=data.get("city", "").strip(),
                    state=data.get("state", "").strip(),
                    country=data.get("country", "").strip(),
                    postal_code=data.get("postal_code", "").strip(),
                )

            # -----------------------------
            # Calculate totals
            # -----------------------------
            subtotal = Decimal("0.00")
            order_items = []

            for item in items_data:

                product_id = item.get("product")
                quantity = int(item.get("quantity", 1))

                if quantity <= 0:
                    return Response(
                        {"error": "Quantity must be greater than 0"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    return Response(
                        {"error": f"Product {product_id} not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                item_total = product.price * quantity
                subtotal += item_total

                order_items.append({
                    "product": product,
                    "quantity": quantity,
                    "price": product.price,
                })

            # -----------------------------
            # Shipping fee
            # -----------------------------
            try:
                shipping_fee = Decimal(
                    str(data.get("shipping_fee", "0"))
                )
            except InvalidOperation:
                shipping_fee = Decimal("0")

            total = subtotal + shipping_fee

            # -----------------------------
            # Ensure session exists
            # -----------------------------
            if not request.session.session_key:
                request.session.create()

            # -----------------------------
            # Create Order
            # -----------------------------
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                address=address,
                payment_method=data.get(
                    "payment_method",
                    "card"
                ).lower(),
                full_name=data.get("full_name", "").strip(),
                phone=data.get("phone", "").strip(),
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total=total,
            )

            # -----------------------------
            # Create Order Items
            # -----------------------------
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product=item["product"],
                    price=item["price"],
                    quantity=item["quantity"],
                )
                for item in order_items
            ])

            serializer = OrderSerializer(
                order,
                context={"request": request}
            )

            return Response(
                {
                    "message": "Order created successfully",
                    "order": serializer.data,
                },
                status=status.HTTP_201_CREATED
            )

    except Exception as e:
        return Response(
            {
                "error": "Order creation failed",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================================
# LIST ORDERS
# =========================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_orders(request):
    try:
        orders = Order.objects.filter(
            user=request.user
        ).order_by("-created_at")

        serializer = OrderSerializer(
            orders,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================================
# ORDER DETAIL
# =========================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_detail(request, pk):
    try:
        order = Order.objects.get(
            pk=pk,
            user=request.user
        )

        serializer = OrderSerializer(
            order,
            context={"request": request}
        )

        return Response(serializer.data)

    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================================
# CREATE PAYMENT
# =========================================
@api_view(["POST"])
@permission_classes([AllowAny])
def create_payment(request):

    order_id = request.data.get("order")

    if not order_id:
        return Response(
            {"error": "Order ID is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:

        # -----------------------------
        # Find Order
        # -----------------------------
        if request.user.is_authenticated:
            order = Order.objects.get(
                id=order_id,
                user=request.user
            )
        else:
            order = Order.objects.get(id=order_id)

    except Order.DoesNotExist:
        return Response(
            {"error": "Order not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    # -----------------------------
    # Already Paid
    # -----------------------------
    if order.is_paid:
        return Response(
            {"error": "Order already paid"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # Existing Pending Payment
    # -----------------------------
    existing_payment = Payment.objects.filter(
        order=order,
        status="PENDING"
    ).first()

    if existing_payment:
        return Response(
            {
                "reference": existing_payment.transaction_id,
                "amount": int(existing_payment.amount * 100),
                "email": (
                    request.user.email
                    if request.user.is_authenticated
                    else "guest@example.com"
                )
            },
            status=status.HTTP_200_OK
        )

    # -----------------------------
    # Create New Payment
    # -----------------------------
    reference = str(uuid.uuid4())

    payment = Payment.objects.create(
        order=order,
        amount=order.total,
        method="CARD",
        transaction_id=reference,
        status="PENDING",
    )

    email = (
        request.user.email
        if request.user.is_authenticated
        else "guest@example.com"
    )

    return Response(
        {
            "message": "Payment initialized",
            "reference": reference,
            "amount": int(payment.amount * 100),
            "email": email,
        },
        status=status.HTTP_201_CREATED
    )


# =========================================
# VERIFY PAYMENT
# =========================================
@api_view(["POST"])
@permission_classes([AllowAny])
def verify_payment(request):

    reference = request.data.get("reference")

    if not reference:
        return Response(
            {"error": "Payment reference is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # Find Payment
    # -----------------------------
    try:
        payment = Payment.objects.select_related(
            "order"
        ).get(transaction_id=reference)

    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    order = payment.order

    # -----------------------------
    # Already Verified
    # -----------------------------
    if payment.status == "COMPLETED":
        return Response(
            {
                "message": "Payment already verified",
                "order_id": order.id,
            },
            status=status.HTTP_200_OK
        )

    # -----------------------------
    # Verify with Paystack
    # -----------------------------
    url = f"https://api.paystack.co/transaction/verify/{reference}"

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        paystack_response = requests.get(
            url,
            headers=headers,
            timeout=30
        )

        paystack_response.raise_for_status()

        response_data = paystack_response.json()

    except requests.exceptions.RequestException as e:
        return Response(
            {
                "error": "Paystack connection failed",
                "details": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # -----------------------------
    # Validate response
    # -----------------------------
    if not response_data.get("status"):
        return Response(
            {
                "error": "Verification failed",
                "details": response_data.get("message"),
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    payment_data = response_data.get("data", {})

    if payment_data.get("status") != "success":
        return Response(
            {"error": "Payment not successful"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # Validate amount
    # -----------------------------
    paystack_amount = Decimal(
        str(payment_data.get("amount", 0))
    ) / Decimal("100")

    if paystack_amount != order.total:
        return Response(
            {
                "error": "Amount mismatch",
                "expected": str(order.total),
                "received": str(paystack_amount),
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # Complete Payment
    # -----------------------------
    payment.status = "COMPLETED"
    payment.save()

    order.is_paid = True
    order.status = "PROCESSING"
    order.save()

    return Response(
        {
            "message": "Payment verified successfully",
            "order_id": order.id,
            "reference": reference,
        },
        status=status.HTTP_200_OK
    )


# =========================================
# PAYSTACK WEBHOOK
# =========================================
@api_view(["POST"])
@permission_classes([AllowAny])
def payment_webhook(request):

    payload = request.body

    signature = request.headers.get(
        "x-paystack-signature"
    )

    computed_signature = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode("utf-8"),
        payload,
        hashlib.sha512
    ).hexdigest()

    if computed_signature != signature:
        return Response(
            {"error": "Invalid signature"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        data = json.loads(payload)

    except json.JSONDecodeError:
        return Response(
            {"error": "Invalid JSON payload"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if data.get("event") != "charge.success":
        return Response(
            {"message": "Event ignored"},
            status=status.HTTP_200_OK
        )

    payment_data = data.get("data", {})

    reference = payment_data.get("reference")

    if not reference:
        return Response(
            {"error": "Reference missing"},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        payment = Payment.objects.select_related(
            "order"
        ).get(transaction_id=reference)

    except Payment.DoesNotExist:
        return Response(
            {"error": "Payment not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    order = payment.order

    if payment.status == "COMPLETED":
        return Response(
            {"message": "Already processed"},
            status=status.HTTP_200_OK
        )

    amount = Decimal(
        str(payment_data.get("amount", 0))
    ) / Decimal("100")

    if amount != order.total:
        return Response(
            {"error": "Amount mismatch"},
            status=status.HTTP_400_BAD_REQUEST
        )

    payment.status = "COMPLETED"
    payment.save()

    order.is_paid = True
    order.status = "PROCESSING"
    order.save()

    return Response(
        {"message": "Webhook processed successfully"},
        status=status.HTTP_200_OK
    )