from django.conf import settings
from django.db import models
from products.models import Product


class RecentlyViewedProduct(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recently_viewed_products')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
