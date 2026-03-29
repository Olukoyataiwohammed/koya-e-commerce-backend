from .models import Cart, CartItem

def get_or_create_cart(request):
    # Logged-in user → user cart
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, defaults={'session_key': None})
        return cart

    # Guest → session cart
    if not request.session.session_key:
        request.session.create()

    cart, _ = Cart.objects.get_or_create(
        session_key=request.session.session_key,
        user=None
    )
    return cart


def merge_guest_cart_to_user(user, session_key):
    if not session_key:
        return

    guest_cart = Cart.objects.filter(
        session_key=session_key,
        user=None
    ).first()
    if not guest_cart:
        return

    user_cart, _ = Cart.objects.get_or_create(user=user)

    for guest_item in guest_cart.items.all():
        user_item, _ = CartItem.objects.get_or_create(
            cart=user_cart,
            menu_item=guest_item.menu_item  # ensure field name matches your model
        )
        user_item.quantity += guest_item.quantity
        user_item.save()

    guest_cart.delete()
