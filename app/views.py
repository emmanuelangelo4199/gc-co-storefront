from django.shortcuts import render, redirect
from .models import Product, userAccount
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import get_user_model

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


def my_homeView(request):
    product = Product.objects.all()
    product_count = product.count()
    context = {
        'product': product,
        'product_count': product_count
    }

    return render(request, 'app/home.html', context)

def productDetails(request):
    context = {}

    return render(request, 'app/product_detail.html', context)

def loginFormWithSignup(request): 
    if request.method == 'POST':

        # register form
        if 'fullname' in request.POST:
            fullname = request.POST.get('fullname', '').strip()
            email = request.POST.get('email', '').strip().lower()
            phone = request.POST.get('phone', '').strip()
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')

            if not all([fullname, email, phone, password, confirm_password]):
                messages.error(request, "Please fill in all fields.")
                return render(request, 'app/login_signup.html')

            if password != confirm_password:
                messages.error(request, "Password does not match.")
                return render(request, 'app/login_signup.html')

            if User.objects.filter(email=email).exists():
                messages.error(request, "an account with this email already exist.")
                return render(request, 'app/login_signup.html')

            if User.objects.filter(phone_number=phone).exists():
                messages.error(request, "An account with this phone already exist.")
                return render(request, 'app/login_signup.html')

            try:    
                validate_password(password)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, 'app/login_signup.html')

            # creating a user
            # the abstractUser still requires a username
            # username = email simply way to implement this
            # username = email.spilt('@')[0] + str(User.objects.count() + 1)

            username = email 

            user = User.objects.create_user(username=username, first_name=fullname, last_name='', email=email,phone_number=phone, password=password)


            login(request, user)
            messages.success(request, "Account created successfully")
            return redirect('app:home')

        # login form
        else:
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password')

            if not email or not password:
                messages.error(request, "Please enter both email and password")
                return render(request, 'app/login_signup.html')

            # USERNAME_FIELD = 'email'
            user = authenticate(request, email=email, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, "Welcome back!!!")
                return redirect('app:home')

            else:
                messages.error(request, "Invalid email or password")
                return render(request, 'app/login_signup.html')

        
    return render(request, 'app/login_signup.html')

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You've been loggedout.")

    if request.user.is_authenticated:
        return redirect('app:home')
    return redirect('app:loginPage')
    
