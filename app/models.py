from django.contrib.auth.models import AbstractUser
import uuid
from django.db import models



class Product(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)


    @property
    def discount_percent(self):
        if self.discount_price and self.discount_price < self.price:
            return int((self.price - self.discount_price) / self.price * 100)
        return 0
    

    def __str__(self):
        return self.name

class userAccount(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number']

    def __str__(self):
        return self.email

class Order(models.Model):
    class Status(models.TextChoices):
        ORDER_CONFIRMED  = 'order confirmed', 'Order Confirmed'
        PROCESSING_PACKAGING = 'processing packaging', 'Processing Package'
        OUT_FOR_DELIVERY = 'out for delivery', 'Out for Delivery'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class payment_Method(models.TextChoices):
        CARD = 'card', 'Card'
        MOBILE_MONEY = 'momo', 'Momo'
        CASH = 'cash', 'Cash'

    class payment_Status(models.TextChoices):
        PAID = 'paid', 'Paid'
        UNPAID = 'unpaid', 'Unpaid'
        REFUND = 'refund', 'Refund'

    order_number = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(userAccount, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDER_CONFIRMED)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.CharField(max_length=50, null=False)
    digital_address = models.CharField(max_length=50, null=False)
    payment_method = models.CharField(max_length=20, choices=payment_Method.choices, default=payment_Method.CARD)
    payment_status = models.CharField(max_length=20, choices=payment_Status.choices, default=payment_Status.UNPAID)
    order_date = models.DateTimeField(auto_now_add=True)
    estimated_delivery_date = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15)


class Order_Items(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)


class Cart(models.Model):
    user = models.ForeignKey(userAccount, on_delete=models.CASCADE, null=True,blank=True)
    session_key = models.CharField(max_length=40, db_index=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class cart_Items(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)