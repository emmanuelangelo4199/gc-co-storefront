from django.urls import path
from .views import my_homeView, productDetails, loginFormWithSignup, logout_view


app_name = 'app'
urlpatterns = [
    path('', my_homeView, name='home'),
    path('products/', productDetails, name='product'),
    path('accounts/', loginFormWithSignup, name='loginPage'),
    path('logout/', logout_view, name='logout')
]
