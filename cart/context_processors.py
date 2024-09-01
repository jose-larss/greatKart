from cart.models import Cart, CartItem
from cart.views import _cart_id

def counter_cart(request):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        number_item_cart = CartItem.objects.filter(cart= cart).count()
    except Cart.DoesNotExist or CartItem.DoesNotExist:
        number_item_cart = 0

    return {'number_item_cart':number_item_cart}