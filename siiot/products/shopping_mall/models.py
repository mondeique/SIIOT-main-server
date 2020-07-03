from django.db import models


def shoppingmall_directory_path(instance, filename):
    return 'shop/{}/thumbnail_{}'.format(instance.id, filename)


class ShoppingMall(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=100, null=True, blank=True)
    order = models.PositiveIntegerField(unique=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image = models.ImageField(null=True, blank=True, upload_to=shoppingmall_directory_path)

    def __str__(self):
        return self.name
