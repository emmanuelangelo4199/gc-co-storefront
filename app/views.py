from django.shortcuts import render



def my_homeView(request):
    context = {}

    return render(request, 'app/home.html', context)

def productDetails(request):
    context = {}

    return render(request, 'app/product_detail.html', context)

def loginFormWithSignup(request): 
    context = {}

    return render(request, 'app/login_signup.html', context)
    
