from rest_framework import serializers, exceptions
from products.shopping_mall.models import ShoppingMall


class ShoppingMallSerializer(serializers.ModelSerializer):
    class Meta:
        class Meta:
            model = ShoppingMall
            fields = '__all__'
