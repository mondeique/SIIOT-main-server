from rest_framework import serializers, exceptions

from mypage.models import Accounts
from products.banner.models import MainBanner
from products.category.models import FirstCategory, SecondCategory, Size, Color, Bank


class BannerSerializer(serializers.ModelSerializer):

    class Meta:
        model = MainBanner
        fields = ['id', 'image_url', 'order']
