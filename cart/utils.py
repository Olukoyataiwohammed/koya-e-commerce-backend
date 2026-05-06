from .models import Cart, CartItem


def get_or_create_cart(request):
    """
    Returns a cart for both authenticated users and guests.
    Ensures guest carts always have a valid session_key.
    """

    # 🔹 Logged-in user → user cart
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(
            user=request.user,
            defaults={"session_key": None}
        )
        return cart

    # 🔹 Guest user → session-based cart
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(
        session_key=session_key,
        user=None
    )

    return cart


def merge_guest_cart_to_user(user, session_key):
    """
    Merge guest cart into user cart after login.
    """

    if not session_key:
        return

    guest_cart = Cart.objects.filter(
        session_key=session_key,
        user=None
    ).first()

    if not guest_cart:
        return

    # 🔹 Get or create user's cart
    user_cart, _ = Cart.objects.get_or_create(user=user)

    for guest_item in guest_cart.items.all():
        
        user_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            product=guest_item.product
        )

        if not created:
            user_item.quantity += guest_item.quantity
        else:
            user_item.quantity = guest_item.quantity

        user_item.save()

    # 🔹 Delete guest cart after merge
    guest_cart.delete()