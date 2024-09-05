from django.contrib import messages, auth
from django.shortcuts import render, redirect
from accounts.forms import RegistrationForm
from accounts.models import Account
from django.contrib.auth.decorators import login_required

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['first_name']
            username = email.split("@")[0]

            user = Account.objects.create_user(first_name=first_name,
                                               last_name=last_name,
                                               email=email,
                                               username=username,
                                               password=password
                                               )
            user.phone_number = phone_number
            user.save()
            
            messages.success(request, "Registration Successfull")
            return redirect('register')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form':form})


def login(request):
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)
        print(user)
        if user is not None:
            auth.login(request, user)

            messages.success(request, "Your are now Login")
            print('pasa por login')
            return redirect('home') #actualmente aqui mas tarde ira a dashboard
        else:
            messages.error(request, "Invalid Login credentials")
            return redirect('login')

    return render(request, 'accounts/login.html')


@login_required(login_url='login')
def logout(request):
    auth.logout(request)
    messages.success(request, "You are Logged Out")
    return redirect('login')
