import uuid

from django.conf import settings
from django.db.models import Avg
from rest_framework import serializers, exceptions
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from crawler.models import CrawlProduct
from products.models import Product, ProductImages
from products.supplymentary.models import PurchasedReceipt, PurchasedTime


class ProductFirstSaveSerializer(serializers.ModelSerializer):
    seller = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        fields = ['seller', 'upload_type', 'condition', 'shopping_mall', 'product_url']


class CrawlDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = CrawlProduct
        fields = ['thumbnail_image_url',
                  'product_name',
                  'int_price']


class ProductUploadDetailInfoSerializer(serializers.ModelSerializer):
    """
    상품 업로드 과정 중 크롤링된 정보 + (option)구매내역 key를 보여주는 serializer 입니다.
    임시저장 불러올 때는 사용 x
    """
    receipt_image_url = serializers.SerializerMethodField()
    crawl_data = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id',
                  'crawl_data',
                  'receipt_image_url',
                  ]

    def get_receipt_image_url(self, instance):
        if instance.receipt:
            return instance.receipt.image_url
        else:
            return None

    def get_crawl_data(self, instance):
        serializer = CrawlDataSerializer(CrawlProduct.objects.get(id=instance.crawl_product_id))
        return serializer.data


class ProductTempUploadDetailInfoSerializer(serializers.ModelSerializer):
    """
    아마도 임시저장 불러올 때 사용할 것 같음. UploadDetail과 합쳐서 한번에 쓸 수 있었는데 분리한 이유는
    임시저장의 경우 업로드 타입에 따라 아마 client에서 action을 다르게 해야 하기 떄문에 일단 구분함
    * 참고 : crawl_product_name 대신 name으로 통합함: name 작성했던게 있으면 name, 없으면 crawl product name
    
    ** category, purchased_time 같이 다른 모델 참고하는 필드는 int(id) 주는데 클라에서 어떻게 할 건지 얘기필요
    % python class 목적에 맞게 구현하였으나, 오류가 나면 수정 필요함.
    """
    receipt_image_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    crawl_data = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    purchased_year = serializers.SerializerMethodField()
    purchased_month = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id',
                  'upload_type', 'condition', 'shopping_mall', 'product_url',
                  'crawl_data',
                  'receipt_image_url',
                  'images',
                  'name',
                  'price', 'content', 'free_delivery',
                  'category', 'color', 'size', 'purchased_year', 'purchased_month'
                  ]

    def get_crawl_data(self, instance):
        serializer = CrawlDataSerializer(CrawlProduct.objects.get(id=instance.crawl_product_id))
        return serializer.data

    def get_receipt_image_url(self, instance):
        if instance.receipt:
            return instance.receipt.image_url
        else:
            return None

    def get_images(self, instance):
        if not instance.images.exists():
            return []
        images = instance.images.all()
        return ProductImagesRetrieveSerializer(images, many=True).data

    def get_name(self, instance):
        if instance.name:
            return instance.name
        return CrawlProduct.objects.get(id=instance.crawl_product_id).product_name

    def get_purchased_month(self, instance):
        if hasattr(instance, 'purchased_time'):
            time = instance.purchased_time
            month = time.month
            return month
        return None

    def get_purchased_year(self, instance):
        if hasattr(instance, 'purchased_time'):
            time = instance.purchased_time
            year = time.year
            return year
        return None


class ProductSaveSerializer(serializers.ModelSerializer):
    """
    상품 임시저장 및 최종저장 시 사용하는 serializer 입니다.
    * purchased time의 경우 purchased_year, purchased_month를 입력받아 서버에서 따로 저장합니다.
    * category 의 경우 second_category의 id 를 받습니다.
    """
    class Meta:
        model = Product
        fields = ['name', 'price', 'content', 'free_delivery',
                  'category', 'color', 'size', 'purchased_time', 'possible_upload', 'temp_save']

    def update(self, instance, validated_data):
        year = validated_data.pop('purchased_year', None)
        month = validated_data.pop('purchased_month', None)
        product = super(ProductSaveSerializer, self).update(instance, validated_data)

        # purchased time save
        if year and month:
            time, _ = PurchasedTime.objects.get_or_create(year=int(year), month=int(month))
            product.purchased_time = time
            product.save()

        return product


class ReceiptSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchasedReceipt
        fields = ['receipt_image_key']


class ProductImageSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = '__all__'


class ProductImagesRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ('image_key', )


class ProductRetrieveSerializer(serializers.ModelSerializer):

    class Meta:
        model = Product
        fields = ('')