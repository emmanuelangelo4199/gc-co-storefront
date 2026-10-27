from decimal import Decimal
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db.models import F
from django.views.decorators.http import require_POST

from .models import Product, SavedItem, cart_Items, Cart, Category, Order, Order_Items
from .utils import get_cart

User = get_user_model()

FREE_SHIPPING_THRESHOLD = Decimal('300.00')
STANDARD_SHIPPING = Decimal('30.00')
TAX_RATE = Decimal('0.03')


def get_cart_data(cart, user=None):
    items = (
        cart_Items.objects.filter(cart=cart)
        .select_related('product', 'product__category')
        if cart
        else cart_Items.objects.none()
    )

    items = list(items)
    subtotal = Decimal('0.00')
    item_count = 0
    for item in items:
        item.line_total = item.product.unit_price * item.quantity
        subtotal += item.line_total
        item_count += item.quantity

    qualifies_free_shipping = subtotal >= FREE_SHIPPING_THRESHOLD and item_count > 0
    shipping = Decimal('0.00') if (qualifies_free_shipping or item_count == 0) else STANDARD_SHIPPING
    amount_to_free_shipping = max(FREE_SHIPPING_THRESHOLD - subtotal, Decimal('0.00')) if item_count > 0 else FREE_SHIPPING_THRESHOLD
    free_shipping_progress = (
        min((subtotal / FREE_SHIPPING_THRESHOLD) * Decimal('100'), Decimal('100'))
        if FREE_SHIPPING_THRESHOLD and item_count > 0
        else Decimal('0')
    )
    tax = (subtotal * TAX_RATE).quantize(Decimal('0.01'))
    grand_total = subtotal + shipping + tax

    if user and user.is_authenticated:
        saved_items = (
            SavedItem.objects.filter(user=user)
            .select_related('product', 'product__category')
        )
    else:
        saved_items = SavedItem.objects.none()

    return {
        'cart_item': items,
        'item_count': item_count,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'grand_total': grand_total,
        'qualifies_free_shipping': qualifies_free_shipping,
        'amount_to_free_shipping': amount_to_free_shipping,
        'free_shipping_progress': free_shipping_progress,
        'free_shipping_threshold': FREE_SHIPPING_THRESHOLD,
        'saved_items': saved_items,
    }


def merge_cart(request, user):
    session_key = request.session.session_key
    if not session_key:
        return
    session_cart = Cart.objects.filter(session_key=session_key, user=None).first()
    if not session_cart:
        return
    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in session_cart.cart_items_set.all():
        existing = cart_Items.objects.filter(cart=user_cart, product=item.product).first()
        if existing:
            existing.quantity += item.quantity
            existing.save()
        else:
            item.cart = user_cart
            item.save()
    session_cart.delete()


def my_homeView(request):
    product = Product.objects.filter(is_active=True).select_related('category')
    product_count = product.count()
    context = {
        'product': product,
        'product_count': product_count,
        'active_category': 'all',
    }
    return render(request, 'app/home.html', context)


def productDetails(request):
    context = {}
    return render(request, 'app/product_detail.html', context)


def loginFormWithSignup(request):
    if request.method == 'POST':
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
                messages.error(request, "An account with this email already exists.")
                return render(request, 'app/login_signup.html')

            if User.objects.filter(phone_number=phone).exists():
                messages.error(request, "An account with this phone already exists.")
                return render(request, 'app/login_signup.html')

            try:
                validate_password(password)
            except ValidationError as e:
                for error in e.messages:
                    messages.error(request, error)
                return render(request, 'app/login_signup.html')

            user = User.objects.create_user(
                username=email,
                first_name=fullname,
                last_name='',
                email=email,
                phone_number=phone,
                password=password
            )

            login(request, user)
            merge_cart(request, user)
            messages.success(request, "Account created successfully.")
            return redirect('app:home')

        else:
            email = request.POST.get('email', '').strip().lower()
            password = request.POST.get('password')

            if not email or not password:
                messages.error(request, "Please enter both email and password.")
                return render(request, 'app/login_signup.html')

            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                merge_cart(request, user)
                messages.success(request, "Welcome back!")
                return redirect('app:home')
            else:
                messages.error(request, "Invalid email or password.")
                return render(request, 'app/login_signup.html')

    return render(request, 'app/login_signup.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.info(request, "You have been logged out.")

    if request.user.is_authenticated:
        return redirect('app:home')
    return redirect('app:loginPage')


def cart_items(request):
    cart = get_cart(request)
    data = get_cart_data(cart, request.user)

    cart_product_ids = [item.product_id for item in data['cart_item']]
    recommended_products = (
        Product.objects.filter(is_active=True)
        .exclude(id__in=cart_product_ids)
        .order_by('-is_featured', '-is_bestseller', '-created_at')[:2]
    )

    context = {
        **data,
        'recommended_products': recommended_products,
    }
    return render(request, 'app/cart.html', context)


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_cart(request, create=True)
    item, created = cart_Items.objects.get_or_create(
        cart=cart, product=product, defaults={'quantity': 1}
    )
    if not created:
        item.quantity = F('quantity') + 1
        item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_total_quantity = cart.cart_items_set.aggregate(Sum('quantity'))['quantity__sum'] or 0
        return JsonResponse({'success': True, 'cart_total_quantity': cart_total_quantity})

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'app:home'
    return redirect(next_url)


@require_POST
def update_cart_quantity(request, item_id):
    cart = get_cart(request)
    if not cart:
        return JsonResponse({'success': False, 'error': 'Cart not found'}, status=404)

    item = get_object_or_404(cart_Items, id=item_id, cart=cart)

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
            new_qty = int(payload.get('quantity', item.quantity))
        else:
            new_qty = int(request.POST.get('quantity', item.quantity))
    except (ValueError, TypeError):
        new_qty = 1

    if new_qty < 1:
        new_qty = 1
    if item.product.stock_quantity > 0 and new_qty > item.product.stock_quantity:
        new_qty = item.product.stock_quantity

    item.quantity = new_qty
    item.save()

    data = get_cart_data(cart, request.user)
    line_total = item.product.unit_price * item.quantity

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'quantity': item.quantity,
            'line_total': f"{line_total:.2f}",
            'item_count': data['item_count'],
            'subtotal': f"{data['subtotal']:.2f}",
            'shipping': f"{data['shipping']:.2f}",
            'tax': f"{data['tax']:.2f}",
            'grand_total': f"{data['grand_total']:.2f}",
            'qualifies_free_shipping': data['qualifies_free_shipping'],
            'amount_to_free_shipping': f"{data['amount_to_free_shipping']:.2f}",
            'free_shipping_progress': float(data['free_shipping_progress']),
            'cart_total_quantity': data['item_count'],
        })

    return redirect('app:carts')


@require_POST
def remove_from_cart(request, item_id):
    cart = get_cart(request)
    if not cart:
        return JsonResponse({'success': False, 'error': 'Cart not found'}, status=404)

    item = get_object_or_404(cart_Items, id=item_id, cart=cart)
    item.delete()

    data = get_cart_data(cart, request.user)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        return JsonResponse({
            'success': True,
            'item_id': item_id,
            'item_count': data['item_count'],
            'subtotal': f"{data['subtotal']:.2f}",
            'shipping': f"{data['shipping']:.2f}",
            'tax': f"{data['tax']:.2f}",
            'grand_total': f"{data['grand_total']:.2f}",
            'qualifies_free_shipping': data['qualifies_free_shipping'],
            'amount_to_free_shipping': f"{data['amount_to_free_shipping']:.2f}",
            'free_shipping_progress': float(data['free_shipping_progress']),
            'cart_total_quantity': data['item_count'],
        })

    return redirect('app:carts')


@require_POST
def clear_cart(request):
    cart = get_cart(request)
    if cart:
        cart.cart_items_set.all().delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_total_quantity': 0})

    return redirect('app:carts')


@require_POST
def save_for_later(request, item_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to save items for later.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'login_required'}, status=401)
        return redirect('app:loginPage')

    cart = get_cart(request)
    if not cart:
        return redirect('app:carts')

    item = get_object_or_404(cart_Items, id=item_id, cart=cart)
    SavedItem.objects.get_or_create(user=request.user, product=item.product)
    item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = get_cart_data(cart, request.user)
        return JsonResponse({
            'success': True,
            'item_id': item_id,
            'item_count': data['item_count'],
            'saved_count': data['saved_items'].count(),
            'subtotal': f"{data['subtotal']:.2f}",
            'shipping': f"{data['shipping']:.2f}",
            'tax': f"{data['tax']:.2f}",
            'grand_total': f"{data['grand_total']:.2f}",
            'qualifies_free_shipping': data['qualifies_free_shipping'],
            'amount_to_free_shipping': f"{data['amount_to_free_shipping']:.2f}",
            'free_shipping_progress': float(data['free_shipping_progress']),
            'cart_total_quantity': data['item_count'],
        })

    return redirect('app:carts')


@require_POST
def move_saved_to_cart(request, saved_id):
    if not request.user.is_authenticated:
        return redirect('app:loginPage')

    saved = get_object_or_404(SavedItem, id=saved_id, user=request.user)
    cart = get_cart(request, create=True)
    item, created = cart_Items.objects.get_or_create(
        cart=cart, product=saved.product, defaults={'quantity': 1}
    )
    if not created:
        item.quantity = F('quantity') + 1
        item.save()

    saved.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = get_cart_data(cart, request.user)
        return JsonResponse({
            'success': True,
            'item_count': data['item_count'],
            'saved_count': data['saved_items'].count(),
            'cart_total_quantity': data['item_count'],
        })

    return redirect('app:carts')


@require_POST
def remove_saved_item(request, saved_id):
    if not request.user.is_authenticated:
        return redirect('app:loginPage')

    saved = get_object_or_404(SavedItem, id=saved_id, user=request.user)
    saved.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        saved_count = SavedItem.objects.filter(user=request.user).count()
        return JsonResponse({'success': True, 'saved_count': saved_count})

    return redirect('app:carts')


def checkout_view(request):
    cart = get_cart(request)
    data = get_cart_data(cart, request.user)

    if not data['cart_item']:
        messages.info(request, "Your cart is empty. Add items before checking out.")
        return redirect('app:carts')

    if request.method == 'POST':
        fullname = request.POST.get('shipping_fullname', '').strip()
        phone = request.POST.get('shipping_phone', '').strip()
        email = request.POST.get('shipping_email', '').strip()
        address = request.POST.get('shipping_address', '').strip()
        city = request.POST.get('shipping_city', '').strip()
        region = request.POST.get('shipping_region', '').strip()
        gps = request.POST.get('shipping_gps', '').strip()
        payment_method = request.POST.get('payment_method', 'momo')

        if not all([fullname, phone, address, gps]):
            messages.error(request, "Please fill in all required delivery details.")
            return render(request, 'app/checkout.html', data)

        full_address = f"{address}, {city}, {region}".strip(', ')

        # Map payment method choice
        valid_methods = {'momo': Order.payment_Method.MOBILE_MONEY,
                         'card': Order.payment_Method.CARD,
                         'cash': Order.payment_Method.CASH}
        selected_method = valid_methods.get(payment_method, Order.payment_Method.MOBILE_MONEY)

        # Create Order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            total_amount=data['grand_total'],
            subtotal=data['subtotal'],
            tax_amount=data['tax'],
            shipping_cost=data['shipping'],
            shipping_address=full_address,
            digital_address=gps,
            payment_method=selected_method,
            payment_status=Order.payment_Status.PAID if selected_method != Order.payment_Method.CASH else Order.payment_Status.UNPAID,
            phone_number=phone,
        )

        # Create Order Items and adjust stock
        for item in data['cart_item']:
            Order_Items.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.product.unit_price,
            )
            if item.product.stock_quantity >= item.quantity:
                item.product.stock_quantity = F('stock_quantity') - item.quantity
                item.product.save()

        # Clear cart
        cart.cart_items_set.all().delete()

        return redirect('app:order_confirmation', order_number=order.order_number)

    return render(request, 'app/checkout.html', data)


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    order_items = Order_Items.objects.filter(order=order).select_related('product', 'product__category')
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'app/order_confirmation.html', context)


def my_orders(request):
    if not request.user.is_authenticated:
        messages.info(request, "Please log in to view your orders.")
        return redirect('app:loginPage')

    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'app/home.html', {'orders': orders})


def category_view(request, slug):
    products = Product.objects.filter(is_active=True).select_related('category')

    if slug == 'all':
        pass
    elif slug == 'sale':
        products = products.filter(discount_price__gt=0)
    else:
        get_object_or_404(Category, slug=slug)
        products = products.filter(category__slug=slug)

    context = {
        'product': products,
        'product_count': products.count(),
        'active_category': slug,
    }
    return render(request, 'app/home.html', context)
