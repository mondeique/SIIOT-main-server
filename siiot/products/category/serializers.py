from rest_framework import serializers, exceptions

from products.category.models import FirstCategory, SecondCategory, Size, Color
from products.shopping_mall.models import ShoppingMall


class FirstCategorySerializer(serializers.ModelSerializer):
    child = serializers.SerializerMethodField()

    class Meta:
        model = FirstCategory
        fields = ['id', 'name', 'child']

    def get_child(self, obj):
        if obj.second_categories.exists():
            return True
        return False


class SecondCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SecondCategory
        fields = ['name', 'id']


class SizeSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Size
        fields = ['id', 'name']

    def get_name(self, obj):
        if obj.size_max:
            return "{} ({}-{})".format(obj.size_name, obj.size, obj.size_max)
        if obj.category.name in ['BAG', 'ACCESSORY', 'JEWELRY']:
            return '없음'
        return "{} ({})".format(obj.size_name, obj.size)


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'color', 'image']
