from django.urls import path
from .views import cart_items, my_homeView, productDetails, loginFormWithSignup, logout_view, add_to_cart, category_view


app_name = 'app'
urlpatterns = [
    path('', my_homeView, name='home'),
    path('products/', productDetails, name='product'),
    path('accounts/', loginFormWithSignup, name='loginPage'),
    path('logout/', logout_view, name='logout'),
    path('cart/', cart_items, name='carts'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('category/<slug:slug>/', category_view, name='category'),
]
