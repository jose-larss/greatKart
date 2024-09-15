from cart.models import Cart, CartItem
from cart.views import _cart_id

def counter_cart(request):
    number_item_cart = 0
    try:
        if request.user.is_authenticated:
            item_cart = CartItem.objects.filter(user=request.user)
        else:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            item_cart = CartItem.objects.filter(cart= cart[:1])

        number_item_cart = len(item_cart)

    except Cart.DoesNotExist or CartItem.DoesNotExist:
        number_item_cart = 0

    return {'number_item_cart':number_item_cart}