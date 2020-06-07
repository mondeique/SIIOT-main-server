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
from products.supplymentary.models import PurchasedReceipt


class ProductFirstSaveSerializer(serializers.ModelSerializer):
    seller = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Product
        fields = ['seller', 'upload_type', 'condition', 'shopping_mall', 'product_url']


class ProductUploadDetailInfoSerializer(serializers.ModelSerializer):
    """
    상품 업로드 시에 크롤링된 정보 + (option)구매내역 key를 보여주는 serializer 입니다.
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
    * 참고 : crawl_product_name 대신 name으로 통합함: name 작성했던게 있으면 name, 없으면 crawl product name
    
    ** category, purchased_time 같이 다른 모델 참고하는 필드는 int(id) 주는데 클라에서 어떻게 할 건지 얘기필요
    """
    receipt_image_url = serializers.SerializerMethodField()
    crawl_thumbnail_image_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    crawl_product_price = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def __init__(self):
        super(ProductTempUploadDetailInfoSerializer, self).__init__()
        self.obj = None
        self.crawl_id = None
        self.c_product = None

    class Meta:
        model = Product
        fields = ['id',
                  'upload_type', 'condition', 'shopping_mall', 'product_url'
                  'crawl_thumbnail_image_url',
                  'receipt_image_url',
                  'images',
                  'name',
                  'crawl_product_price',
                  'price', 'content', 'free_delivery',
                  'category', 'color', 'size', 'purchased_time',
                  ]

    def set_obj(self, instance):
        self.obj = instance

    def crawl_data(self):
        self.crawl_id = self.obj.crawl_product_id
        self.c_product = CrawlProduct.objects.get(id=self.crawl_id)

    def get_receipt_image_url(self, instance):
        if hasattr(instance, 'receipt'):
            return instance.receipt.image_url
        else:
            return None

    def get_images(self, instance):
        if not instance.images.exists():
            return []
        images = instance.images.all()
        return ProductImagesRetrieveSerializer(images, many=True).data

    def get_crawl_thumbnail_image_url(self, instance):
        self.set_obj(instance)
        self.crawl_data()
        return self.c_product.thumbnail_url

    def get_name(self, instance):
        self.set_obj(instance)
        self.crawl_data()
        if self.obj.name:
            return self.obj.name
        return self.c_product.product_name

    def get_crawl_product_price(self):
        return self.c_product.price


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


class ProductImagesRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImages
        fields = ('image_key')

