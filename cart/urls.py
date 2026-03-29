from django.urls import path
from . import views

app_name = "cart"

urlpatterns = [
    path("", views.cart_detail, name="cart-detail"),
    path("add/", views.add_to_cart, name="add-to-cart"),
    path("item/<int:item_id>/", views.update_cart_item, name="update-cart-item"),
    path("item/<int:item_id>/remove/", views.remove_from_cart, name="remove-from-cart"),
    path("clear/", views.clear_cart, name="clear-cart"),
    path("item/<int:item_id>/decrease/", views.decrease_product_from_cart, name="decrease-product-from-cart"),
]
