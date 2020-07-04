from rest_framework import serializers, exceptions

from mypage.models import Accounts
from products.category.models import FirstCategory, SecondCategory, Size, Color, Bank


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
        fields = ['id', 'color', 'color_code']


class AccountsSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Accounts
        fields = '__all__'


class BankListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'bank']