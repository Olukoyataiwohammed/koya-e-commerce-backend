from django.db import models
from django.contrib.auth.models import User
from store.models import Product


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="cart"
    )
    session_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f"Cart of {self.user.username}"
        return f"Guest Cart ({self.session_key})"

    # 🔹 New method: subtotal of cart
    def get_subtotal(self):
        return sum(item.get_total_price() for item in self.items.all())

    # 🔹 New method: total including shipping (can adjust shipping logic later)
    def get_total(self):
        shipping_fee = 0
        return self.get_subtotal() + shipping_fee


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        related_name="items",
        on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product,
        related_name="cart_items",
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    def get_total_price(self):
        return self.quantity * self.product.price