from rest_framework import serializers, exceptions
from products.shopping_mall.models import ShoppingMall
from products.supplymentary.models import ShoppingMallAddRequest


class ShoppingMallDemandSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        class Meta:
            model = ShoppingMallAddRequest
            fields = ['user', 'shoppingmall_name']
