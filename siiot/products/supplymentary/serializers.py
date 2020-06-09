from rest_framework import serializers
from products.supplymentary.models import ShoppingMallAddRequest


class ShoppingMallDemandSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ShoppingMallAddRequest
        fields = ['user', 'shoppingmall_name']
