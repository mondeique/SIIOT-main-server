import datetime

from rest_framework import serializers
from django.contrib.auth import get_user_model

from accounts.models import User
from core.utils import test_thumbnail_image_url, get_age_fun
from crawler.models import CrawlProduct
from products.category.models import Bank
from transaction.models import Transaction
from mypage.models import DeliveryPolicy, Accounts
from payment.models import Wallet
from products.models import Product


class AccountsSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Accounts
        fields = '__all__'


class SimpleAccountsSerializer(serializers.ModelSerializer):
    accounts = serializers.SerializerMethodField()

    class Meta:
        model = Accounts
        fields = ['id', 'accounts']

    def get_accounts(self, obj):
        bank = obj.bank.bank
        accounts = obj.bank_accounts
        return bank + ' ' + accounts


class BankListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = ['id', 'bank']


class SimpleUserInfoSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = User
        fields = ['user_info']

    def get_user_info(self, obj):
        user = obj
        if user.is_anonymous:
            return None
        serializer = SimpleUserInfoSerializer(user)
        return serializer.data


class DeliveryPolicyInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryPolicy
        fields = '__all__'


class TransactionHistorySerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id', 'thumbnail_image_url', 'price', 'name', 'status', 'created_at']

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

    def get_status(self, obj):
        status = obj.status
        if status == 1:
            return '승인 대기중'
        elif status == 2:
            return '배송 준비중'
        elif status == 3:
            return '배송 중'
        elif status == 5:
            return '거래완료'
        elif status in [-1, -2, -3]:
            return '거래취소'
        return None

    def get_price(self, obj):
        deal = obj.deal
        return deal.total

    def get_name(self, obj):
        trades = obj.deal.trades.all()
        if trades.count() > 1:
            name = trades.first().product.name + ' 외 ' + str(trades.count() - 1) + '건'
        else:
            name = trades.first().product.name
        return name

    def get_created_at(self, obj):
        reformed_created_at = datetime.datetime.strftime(obj.created_at, '%y.%m.%d')
        return reformed_created_at


class SoldHistorySerializer(TransactionHistorySerializer):
    other_party_nickname = serializers.SerializerMethodField()

    class Meta(TransactionHistorySerializer.Meta):
        fields = TransactionHistorySerializer.Meta.fields + ['other_party_nickname']

    def get_other_party_nickname(self, obj):
        buyer = obj.deal.buyer
        return buyer.nickname


class PurchasedHistorySerializer(TransactionHistorySerializer):
    other_party_nickname = serializers.SerializerMethodField()

    class Meta(TransactionHistorySerializer.Meta):
        fields = TransactionHistorySerializer.Meta.fields + ['other_party_nickname']

    def get_other_party_nickname(self, obj):
        seller = obj.deal.seller
        return seller.nickname


class WalletHistorySerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    scheduled_date = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = Wallet
        fields = ['id', 'status', 'thumbnail_image_url', 'amount', 'name', 'age', 'buyer_nickname', 'scheduled_date', 'settled_date']

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

    def get_nickname(self, obj):
        seller = obj.deal.seller
        return seller.nickname


class OnSaleProductSerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    sold = serializers.SerializerMethodField()
    uploaded_at = serializers.SerializerMethodField()  # ex: 2020.07.05

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'thumbnail_image_url', 'view_count', 'like_count', 'sold', 'uploaded_at']

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
    def get_view_count(obj):
        if hasattr(obj, 'views'):
            return obj.views.view_counts
        return 0

    @staticmethod
    def get_like_count(obj):
        if obj.liked.exists():
            return obj.liked.all().count()
        return 0

    @staticmethod
    def get_uploaded_at(obj):
        reformat_created_at = datetime.datetime.strftime(obj.created_at, '%y.%m.%d')
        return reformat_created_at

    @staticmethod
    def get_sold(obj):
        status = obj.status
        return status.sold
