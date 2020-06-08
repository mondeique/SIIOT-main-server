from django.db import models


class ShoppingMall(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, null=True, blank=True)
    order = models.PositiveIntegerField(unique=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
