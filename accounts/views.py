import requests
from urllib.parse import urlparse
from django.contrib import messages, auth
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect, get_object_or_404
from accounts.forms import RegistrationForm, UserProfileForm, UserForm
from accounts.models import Account, UserProfile
from cart.models import Cart, CartItem
from orders.models import Order, OrderProduct
from cart.views import _cart_id
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

#Verificationm email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage


@login_required(login_url="login")
def order_detail(request, order_id):
    subtotal = 0
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    for i in order_detail:
        subtotal += i.product.price * i.quantity
    return render(request, "accounts/order_detail.html", {'order_detail':order_detail,
                                                          'order':order,
                                                          'subtotal':subtotal})


@login_required(login_url="login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST['current_password'] 
        new_password = request.POST['new_password'] 
        confirm_password = request.POST['confirm_password'] 

        user = Account.objects.get(username__exact=request.user.username)
        
        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # Auth.logout(request)
                messages.success(request, "Password Updated successfully")
                return redirect('change_password')
            else:
                messages.error(request, "Please Enter a Valid current Password")
                return redirect('change_password')
        else:
            messages.error(request, "Password does not match!")
            return redirect('change_password')
            
    return render(request, "accounts/change_password.html")



@login_required(login_url="login")
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    return render(request, "accounts/my_orders.html", {'orders':orders})



@login_required(login_url="login")
def edit_profile(request):
    userprofile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        user_profile_form = UserProfileForm(request.POST, request.FILES, instance=userprofile)
        if user_form.is_valid() and user_profile_form.is_valid():
            user_form.save()
            user_profile_form.save()
            messages.success(request, "Your Profile has been updated")
            return redirect('edit_profile')

    user_form = UserForm(instance=request.user)
    user_profile_form = UserProfileForm(instance=userprofile)

    return render(request, 'accounts/edit_profile.html', {'user_form':user_form,
                                                          'user_profile_form':user_profile_form,
                                                          'userprofile':userprofile})



def forgotPassword(request):
    if request.method == "POST":
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email) # tiene que ser exacto 

            #Reset Password email
            current_site = get_current_site(request)
            mail_subject = "Reset your Password"
            message = render_to_string('accounts/reset_password_email.html', {
                'user':user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, "Password reset email has been sent to your email address.")
            return redirect('login')

        else:
            messages.error(request, "Account does not exists!")
    return render(request, "accounts/forgotPassword.html")


@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    orders_count = orders.count()
    userprofile = UserProfile.objects.get(user=request.user)
    return render(request, 'accounts/dashboard.html', {'orders':orders, 
                                                       'orders_count':orders_count,
                                                       'userprofile':userprofile})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]

            user = Account.objects.create_user(first_name=first_name,
                                               last_name=last_name,
                                               email=email,
                                               username=username,
                                               password=password
                                               )
            user.phone_number = phone_number
            user.save()

            #User Activation
            current_site = get_current_site(request)
            mail_subject = "PLease activate your account"
            message = render_to_string('accounts/acount_verification_email.html', {
                'user':user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()
            """
            try:
                send_email.send()
                messages.success(request, "Registration Successful. Please check your email to activate your account.")
            except Exception as e:
                messages.error(request, f"Error sending email: {str(e)}")
                return redirect('register')
            """
            #messages.success(request, "thank You fot registering with us. We have sent you a verification email to your email adress. PLase verify it.")
            return redirect('/accounts/login/?command=verification&email='+email)
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form':form})


def login(request):
    ex_var_list = []
    id = []

    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(request, email=email, password=password)
        if user is not None:
            # comprobar si el usuario esta logado y asignar carro
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    
                    #Getting de product variation by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    #Get the cart items from the user to access his product variations
                    cart_item = CartItem.objects.filter(user=user)

                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)
                    print("Ex_var_list es: ",ex_var_list)
                    print(id)
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            print(index)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                                
                            for item in cart_item:
                                item.user = user
                                item.save()
            except:
                pass


            auth.login(request, user) # cuando se autentica cambia el id de sesion

            messages.success(request, "Your are now Login")
            url = request.META.get('HTTP_REFERER')
            try:
                # Parsear la URL para obtener el query string
                query = urlparse(url).query
                # next=/cart/checkout
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    next_page = params['next']
                    return redirect(next_page)
                
            except:
                return redirect('dashboard') #actualmente aqui mas tarde ira a dashboard
            
        else:
            messages.error(request, "Invalid Login credentials")
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You are Logged Out")
    return redirect('login')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(id=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(request, "Configurations! Your Account is activated!!")
        return redirect('login')
    else:
        messages.error(request, "Invalid Activation Link")
        return redirect('register')
    

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(id=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        print(request.session)
        messages.success(request, "Please Reset your Password")
        return redirect('resetPassword')
    else:
        messages.error(request, "This link has been expired")
        return redirect('login')
    

def resetPassword(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(id=uid)
            user.set_password(password)
            user.save()
            messages.success(request, "Password reset successfull")
            return redirect('login')
        else:
            messages.error(request, "Password do not match!")
            return redirect('resetPassword')

    return render(request, "accounts/resetPassword.html")