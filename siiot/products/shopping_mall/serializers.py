from rest_framework import serializers, exceptions

from products.models import Product
from products.shopping_mall.models import ShoppingMall


class ShoppingMallSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingMall
        fields = ['id', 'name', 'domain', 'image']


class ShoppingMallSearchSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingMall
        fields = ['id', 'name', 'domain', 'image', 'count']

    def get_count(self, obj):
        count = Product.objects.filter(shopping_mall=obj).count()
        return count
