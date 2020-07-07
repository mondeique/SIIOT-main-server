from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import User
from core.utils import test_thumbnail_image_url, get_age_fun
from crawler.models import CrawlProduct
from delivery.models import Transaction
from mypage.models import DeliveryPolicy
from payment.models import Wallet
from products.models import Product


class SimpleSellerInfoSerializer(serializers.ModelSerializer):
    profile_img = serializers.SerializerMethodField()
    star_rating = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'profile_img', 'nickname', 'star_rating']

    def get_profile_img(self, obj):
        user = obj
        if hasattr(user, 'profile'):
            return user.profile.profile_img.url
        return None

    def get_star_rating(self, obj):
        # todo: review 만들고 rating 계산
        return 5.0


class MypageSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()
    # sales_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_info']

    def get_user_info(self, obj):
        user = obj
        if user.is_anonymous:
            return None
        serializer = SimpleSellerInfoSerializer(user)
        return serializer.data

    # def get_sales_count(self, obj):
    #     user = obj
    #     if user.is_anonymous:
    #         return None
    #     return user.products.all().count()


class DeliveryPolicyInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryPolicy
        fields = '__all__'


class TransactionHistorySerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'thumbnail_image_url', 'price', 'name', 'age']

    def get_thumbnail_image_url(self, obj):
        self.product = obj.deal.trades.first().product
        if not self.product.crawl_product_id:
            if hasattr(self.product, 'prodthumbnail'):
                return self.product.prodthumbnail.image_url
            # for develop
            try:
                return self.product.images.first().image_url
            except:
                return test_thumbnail_image_url
        return CrawlProduct.objects.get(id=self.product.crawl_product_id).thumbnail_image_url

    def get_price(self, obj):
        self.deal = obj.deal
        return self.deal.remain

    def get_name(self, obj):
        trades = self.deal.trades.all()
        if trades.count() > 1:
            name = trades.first().product.name + ' 외 ' + str(trades.count() - 1) + '건'
        else:
            name = trades.first().product.name
        return name

    def get_age(self, obj):
        return get_age_fun(self.deal)


class TransactionSoldHistorySerializer(TransactionHistorySerializer):
    status = serializers.SerializerMethodField()
    buyer_nickname = serializers.SerializerMethodField()
    action_status = serializers.SerializerMethodField()

    class Meta(TransactionHistorySerializer.Meta):
        fields = TransactionHistorySerializer.Meta.fields + ['status', 'buyer_nickname', 'action_status']

    def get_status(self, obj):
        status = obj.status
        if status in [1, 2, 3, 4]:
            return obj.get_status_display()
        elif status in [-2, -3]:
            return '환불완료'
        else:
            return None

    def get_action_status(self, obj): # True 인 경우, 판매승인, 판매 거절 버튼 활성화
        status = obj.status
        if status == 1:
            return 1  # 판매 승인 버튼 활성화 : 판매 거절은 상세 내역에서서
        return 0

    def get_buyer_nickname(self, obj):
        buyer = self.deal.buyer
        return buyer.nickname


class TransactionPurchasedHistorySerializer(TransactionHistorySerializer):
    status = serializers.SerializerMethodField()
    seller_nickname = serializers.SerializerMethodField()
    action_status = serializers.SerializerMethodField()

    class Meta(TransactionHistorySerializer.Meta):
        fields = TransactionHistorySerializer.Meta.fields + ['status', 'seller_nickname', 'action_status']

    def get_status(self, obj):
        status = obj.status
        if status in [1, 2, 3, 4]:
            return obj.get_status_display()
        elif status in [-2, -3]:
            return '환불완료'
        else:
            return None

    def get_action_status(self, obj): # True 인 경우, 판매승인, 판매 거절 버튼 활성화
        status = obj.status
        if status == 1:
            return 1  # 거래 취소 가능
        elif status in [2, 3]:
            return 2  # 구매 확정 가능
        return 0

    def get_seller_nickname(self, obj):
        seller = self.deal.seller
        return seller.nickname


class TransactionSettlementHistorySerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    scheduled_date = serializers.SerializerMethodField()
    buyer_nickname = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'status', 'thumbnail_image_url', 'amount', 'name', 'age', 'buyer_nickname', 'scheduled_date']

    def get_thumbnail_image_url(self, obj):
        product = obj.deal.trades.first()
        if not product.crawl_product_id:
            if hasattr(product, 'prodthumbnail'):
                return product.prodthumbnail.image_url
            # for develop
            try:
                return product.images.first().image_url
            except:
                return test_thumbnail_image_url
        return CrawlProduct.objects.get(id=product.crawl_product_id).thumbnail_image_url

    def get_name(self, obj):
        trades = obj.deal.trades.all()
        if trades.count() > 1:
            name = trades.first().product.name + ' 외 ' + str(trades.count() - 1) + '건'
        else:
            name = trades.first().product.name
        return name

    def get_age(self, obj):
        return get_age_fun(obj.deal)

    def get_scheduled_date(self, obj):
        date = obj.scheduled_date
        return date.strftime('%y-%m-%d')

    def get_buyer_nickname(self, obj):
        buyer = obj.deal.buyer
        return buyer.nickname


class OnSaleProductSerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()  # ex: 3 days ago
    sold = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'thumbnail_image_url', 'views', 'age', 'sold']

    @staticmethod
    def get_thumbnail_image_url(obj):
        if not obj.crawl_product_id:
            if hasattr(obj, 'prodthumbnail'):
                return obj.prodthumbnail.image_url
            # for develop
            try:
                return obj.images.first().image_url
            except:
                return test_thumbnail_image_url
        return CrawlProduct.objects.get(id=obj.crawl_product_id).thumbnail_image_url

    @staticmethod
    def get_views(obj):
        if hasattr(obj, 'views'):
            return obj.views.view_counts
        return 0

    @staticmethod
    def get_age(obj):
        return get_age_fun(obj)

    @staticmethod
    def get_sold(obj):
        status = obj.status
        return status.sold
