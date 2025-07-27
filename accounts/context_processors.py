
# accounts/context_processors.py
from .models import Wishlist
# your_app/context_processors.py
from .models import Cart

def cart_item_count(request):
    cart_items_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.items.count()  # Or sum quantities if you want total items
            # Alternative if you want to sum quantities:
            # cart_items_count = sum(item.quantity for item in cart.items.all())
        except Cart.DoesNotExist:
            pass
    return {'cart_items_count': cart_items_count}


def wishlist_count(request):
    if request.user.is_authenticated:
        return {'wishlist_count': Wishlist.objects.filter(user=request.user).count()}
    return {'wishlist_count': 0}