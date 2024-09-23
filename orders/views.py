import datetime
import json
import random
import string

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from cart.models import CartItem
from orders.models import Order, Payment, OrderProduct
from store.models import Product
from orders.forms import OrderForm

#Verificationm email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

def generar_codigo_alfanumerico(longitud=17):
    caracteres = string.ascii_letters + string.digits  # Letras mayúsculas, minúsculas y dígitos
    codigo = ''.join(random.choices(caracteres, k=longitud))

    return codigo


def order_completed(request):
    subTotal = 0
    order_number = request.GET.get('order_number')  # Uso correcto: request.GET
    payment_id = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order=order)

        for item in order_products:
            subTotal += item.product_price * item.quantity

        return render(request, 'orders/order_completed.html', {'order':order, 
                                                           'order_products':order_products,
                                                           'subTotal':subTotal})
    except (OrderProduct.DoesNotExist, Order.DoesNotExist):
        return redirect('home')
    

def payments(request):
    body = json.loads(request.body)
    print(body)
    transId = generar_codigo_alfanumerico()
    print(transId)
    order = Order.objects.get(user = request.user, is_ordered = False, order_number = body['orderId'])
    # Store Transaction details in payment Model
    payment = Payment.objects.create(
        user = request.user,
        payment_id = transId,
        payment_method = body['payment_method'],
        payment_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the Cart items to Order product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        order_product = OrderProduct.objects.create(
            order_id=order.id,
            payment=payment,
            user_id=request.user.id,
            product_id=item.product.id,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True, 
        )

        product_variations = item.variations.all()
        order_product.variations.set(product_variations)
        order_product.save()

        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
        

    # Clear Cart
    cart_items = CartItem.objects.filter(user=request.user).delete()

    # Send Order received email to customer
    mail_subject = "Thank for your Order!"
    message = render_to_string('orders/order_received_email.html', {
        'user':request.user,
        'order':order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number':order.order_number,
        'transId':transId,
    }
    return JsonResponse(data)


def place_order(request):
    grand_total = 0
    tax = 0
    total = 0
    quantity = 0

    current_user = request.user

    # the cart count es menor o igual a 0, redireccione a store
    cart_items = CartItem.objects.filter(user = current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')
    
    for car_item in cart_items:
        total += (car_item.product.price * car_item.quantity)
        quantity += car_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        
        if form.is_valid():
            # STORE ALL THE BILLING INFORMATION INSIDE oRDER tABLE
            data = form.save(commit=False)

            data.user = current_user
            data.order_total = grand_total
            data.tax = tax  
            data.ip = request.META.get('REMOTE_ADDR')
            # grabacion para extraer el id del Order
            data.save()
           
            # Generate Order Number
            yr = int(datetime.date.today().strftime('%Y')) 
            dt = int(datetime.date.today().strftime('%d'))    
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime('%Y%m%d') #20240305

            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user = current_user, is_ordered = False, order_number= order_number)

            return render(request, 'orders/payments.html', {'order':order, 
                                                            'cart_items':cart_items,
                                                            'total':total,
                                                            'tax':tax,
                                                            'grand_total': grand_total})
        else:
            return redirect('checkout')

            

            

