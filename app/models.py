from django.db import models



class Product(models.Model):
    name = models.CharField(max_length=100, null=False, blank=False)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_sale = models.BooleanField(default=False)
    inventory = models.IntegerField(null=False, blank=False)
    created_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

