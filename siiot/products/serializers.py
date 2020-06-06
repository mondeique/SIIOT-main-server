import uuid

from django.conf import settings
from django.db.models import Avg
from rest_framework import serializers, exceptions
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from products.models import Product, ProductImages
from products.supplymentary.models import PurchasedReceipt


class ProductFirstSaveSerializer(serializers.ModelSerializer):
    seller = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        fields = ['seller', 'upload_type', 'condition', 'shopping_mall', 'product_url']


class ProductUploadDetailInfoSerializer(serializers.ModelSerializer):
    """
    상품 업로드 시에 크롤링된 정보 + (option) 구매내역 key를 보여주는 serializer 입니다.
    임시저장 불러올 때는 사용 x
    """
    receipt_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id',
                  'crawl_thumbnail_image_url',
                  'receipt_image_url',
                  'crawl_product_name',
                  'crawl_product_price',
                  ]

    def get_receipt_image_url(self, instance):
        if hasattr(instance, 'receipt'):
            return instance.receipt.image_url
        else:
            return None


class ProductTempUploadDetailInfoSerializer(serializers.ModelSerializer):
    """
    아마도 임시저장 불러올 때 사용할 것 같음. UploadDetail과 합쳐서 한번에 쓸 수 있었는데 분리한 이유는
    임시저장의 경우 업로드 타입에 따라 아마 client에서 action을 다르게 해야 하기 떄문에 일단 구분함
    """
    class Meta:
        model = Product
        fields = []


class ProductSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'price', 'content', 'free_delivery',
                  'category', 'color', 'size', 'purchased_time',
                  ]


class ReceiptSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasedReceipt
        fields = ['receipt_image_key']


class ProductImageSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = '__all__'
