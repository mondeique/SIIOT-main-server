from django.conf import settings
from django.db import models


class DeliveryPolicy(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name='delivery_policy', on_delete=models.CASCADE)
    general = models.IntegerField(verbose_name='일반')
    mountain = models.IntegerField(verbose_name='산간지역')
