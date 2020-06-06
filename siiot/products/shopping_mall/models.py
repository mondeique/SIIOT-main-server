from django.db import models


class ShoppingMall(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)