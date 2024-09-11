from django.contrib import messages, auth
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect
from accounts.forms import RegistrationForm
from accounts.models import Account
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

#Verificationm email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

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
    return render(request, 'accounts/dashboard.html')


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
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(request, email=email, password=password)
        if user is not None:
            auth.login(request, user)

            messages.success(request, "Your are now Login")
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