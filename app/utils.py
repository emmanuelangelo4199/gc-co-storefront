from .models import Cart

def get_cart(request, create=False):
    if request.user.is_authenticated:
        if create:
            return Cart.objects.get_or_create(user=request.user)[0]
        return Cart.objects.filter(user=request.user).first()

    if not request.session.session_key:
        if not create:
            return None
        request.session.create()

    key = request.session.session_key
    if create:
        return Cart.objects.get_or_create(session_key=key, user=None)[0]
    return Cart.objects.filter(session_key=key, user=None).first()