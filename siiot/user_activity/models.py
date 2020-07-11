from django.conf import settings
from django.db import models
from products.models import Product


class RecentlyViewedProduct(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_viewed_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='recently_viewed_products')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class RecentlySearchedKeyword(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recently_searched_keywords')
    keyword = models.CharField(max_length=100)
    recent = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        super(RecentlySearchedKeyword, self).save(*args, **kwargs)

        # delete exclude recent 3 keywords
        qs_ids = list(RecentlySearchedKeyword.objects.filter(user=self.user).order_by('-updated_at').values_list('pk', flat=True)[:3])
        RecentlySearchedKeyword.objects.filter(user=self.user).exclude(id__in=qs_ids).delete()
