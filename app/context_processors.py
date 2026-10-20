from django.db.models import Sum
from .utils import get_cart

def cart_icon_count(request):
    cart = get_cart(request)
    total = 0
    if cart:
        total = cart.cart_items_set.aggregate(Sum('quantity'))['quantity__sum'] or 0
    return {'cart_total_quantity': total}