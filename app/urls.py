from django.urls import path
from .views import (
    my_homeView,
    productDetails,
    loginFormWithSignup,
    logout_view,
    cart_items,
    add_to_cart,
    update_cart_quantity,
    remove_from_cart,
    clear_cart,
    save_for_later,
    move_saved_to_cart,
    remove_saved_item,
    checkout_view,
    order_confirmation,
    my_orders,
    category_view,
)

app_name = 'app'

urlpatterns = [
    path('', my_homeView, name='home'),
    path('products/', productDetails, name='product'),
    path('accounts/', loginFormWithSignup, name='loginPage'),
    path('logout/', logout_view, name='logout'),
    path('category/<slug:slug>/', category_view, name='category'),

    # Cart
    path('cart/', cart_items, name='carts'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart_quantity, name='update_cart_quantity'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),

    # Saved for Later
    path('cart/save/<int:item_id>/', save_for_later, name='save_for_later'),
    path('cart/saved/move/<int:saved_id>/', move_saved_to_cart, name='move_saved_to_cart'),
    path('cart/saved/remove/<int:saved_id>/', remove_saved_item, name='remove_saved_item'),

    # Checkout & Orders
    path('checkout/', checkout_view, name='checkout'),
    path('order-confirmation/<uuid:order_number>/', order_confirmation, name='order_confirmation'),
    path('my-orders/', my_orders, name='my_orders'),
]
