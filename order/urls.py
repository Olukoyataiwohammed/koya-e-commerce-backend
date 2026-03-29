from django.urls import path
from . import views

urlpatterns = [
    # Orders
    path("create/", views.create_order),
    path("", views.list_orders),
    path("<int:pk>/", views.order_detail),

    # Payments
    path("payment/create/", views.create_payment),
    path("payment/verify/", views.verify_payment),
    path("payment/webhook/", views.payment_webhook),
]