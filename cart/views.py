from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from cart.models import Cart, CartItem

def _cart_id(request):
    cart = request.session.session_key # Codemy cart = self.session.get('session_key')
    if not cart:
        cart = request.session.create() # Codemy cart = self.session['session_key'] = {}

    return cart


def remove_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the sesion
    cart_item = CartItem.objects.get(product=product, cart= cart)
    cart_item.delete()

    return redirect("cart")

def remove_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the sesion

    cart_item = CartItem.objects.get(product=product, cart= cart)
    if cart_item.quantity <= 1:
        cart_item.delete()
    else:
        cart_item.quantity -= 1
        cart_item.save()

    return redirect('cart')


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)

    try: 
        cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using the cart_id present in the sesion
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(product=product, cart= cart)
        cart_item.quantity += 1
        cart_item.save()

    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(product=product, cart= cart, quantity = 1)

    return redirect('cart')

def cart(request, total = 0, quantity = 0, cart_items = None):
    total = 0
    quantity = 0
    tax = 0
    grand_total = 0

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active = True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total) / 100
        grand_total = total + tax
    
    except Cart.DoesNotExist or CartItem.DoesNotExist:
        pass

    return render(request, "store/cart.html", {'total':total, 
                                               'quantity':quantity, 
                                               'cart_items':cart_items,
                                               'tax':tax,
                                               'grand_total':grand_total})
