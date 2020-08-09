from django.conf import settings
from rest_framework import serializers
from accounts.models import User
from mypage.models import DeliveryPolicy, Address
from products.category.serializers import SecondCategorySerializer
from products.models import Product
from products.serializers import ProdThumbnailSerializer
from .models import Trade, Deal, Payment
from payment.loader import load_credential


######## 장바구니 담기 및 카트 조회 serialzier
class SellerForTradeSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'profile']

    def get_profile(self, obj):
        return obj.profile.profile_image_url


class PaymentInfoForTrade(serializers.ModelSerializer):
    class Meta:
        model = DeliveryPolicy
        fields = ['general', 'mountain']


class ProductForTradeSerializer(serializers.ModelSerializer):
    thumbnails = serializers.SerializerMethodField()
    second_category = SecondCategorySerializer(allow_null=True)
    # discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'price',
                  'thumbnails', 'size', 'second_category']

    def get_thumbnails(self, obj):
        if not hasattr(obj, 'prodthumbnail'):
            return {"thumbnail": "https://pepup-server-storages.s3.ap-northeast-2.amazonaws.com/static/img/prodthumbnail_default.png"}
        thumbnails = obj.prodthumbnail
        return ProdThumbnailSerializer(thumbnails).data

    # def get_discounted_price(self,obj):
    #     return obj.discounted_price


class TradeSerializer(serializers.ModelSerializer):
    product = ProductForTradeSerializer(read_only=True)
    status = serializers.SerializerMethodField()
    seller = SellerForTradeSerializer()
    payinfo = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = ('id', 'product', 'seller', 'payinfo', 'status')

    def get_payinfo(self, obj):
        return PaymentInfoForTrade(obj.seller.delivery_policy).data

    def get_status(self, obj):
        status = obj.product.status
        if status.sold:
            return 1
        elif status.purchasing:
            return 2
        elif status.editing:
            return 3
        return 0

######## 장바구니 담기 및 카트 조회 serialzier END


######## 구매 과정 serialzier
class CannotBuyErrorSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = ['name']

    def get_name(self, obj):
        return obj.product.name


class DealSerializer(serializers.ModelSerializer):
    seller = serializers.PrimaryKeyRelatedField(read_only=True)
    trades = serializers.SerializerMethodField()
    total = serializers.IntegerField()
    delivery_charge = serializers.IntegerField()

    class Meta:
        model = Deal
        fields = ['seller', 'trades', 'totol', 'delivery_charge']

    def get_trades(self, obj):
        trades = obj.trade_set.all()
        return trades


class PaymentSerializer(serializers.Serializer):
    trade = serializers.ListField()
    price = serializers.IntegerField()
    address = serializers.CharField()
    memo = serializers.CharField(default='')
    mountain = serializers.BooleanField(default=False)
    application_id = serializers.IntegerField()  # 1: web, 2:android, 3:ios


# payment 에 사용되는 serializer
class ItemSerializer(serializers.ModelSerializer):
    item_name = serializers.SerializerMethodField()
    unique = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    qty = serializers.IntegerField(default=1)

    class Meta:
        model = Trade
        fields = ('item_name', 'unique', 'price', 'qty')

    def get_item_name(self, obj):
        return obj.product.name

    def get_unique(self, obj):
        return str(obj.product.pk)

    def get_price(self, obj):
        return obj.product.price


class PayformSerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField()
    order_id = serializers.IntegerField(source='id')
    items = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    pg = serializers.CharField(default='inicis')
    method = serializers.CharField(default='')

    class Meta:
        model = Payment
        fields = ['price', 'application_id', 'name', 'pg', 'method', 'items', 'user_info', 'order_id']

    def get_items(self, obj):
        items = self.context['items']
        return ItemSerializer(items, many=True).data

    def get_user_info(self, obj):
        return {
            'username': obj.user.nickname,
            'email': obj.user.email,
            'addr': self.context.get('addr'),
            'phone': obj.user.phone
        }

    def get_application_id(self, obj):
        print(self.context.get('application_id'))

        if self.context.get('application_id') == 1:
            return load_credential('application_id_web')
        elif self.context.get('application_id') == 2:
            return load_credential('application_id_android')
        elif self.context.get('application_id') == 3:
            return load_credential('application_id_ios')
        else:
            return ""


class PaymentConfirmSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()
    receipt_id = serializers.CharField()


class PaymentDoneSerialzier(serializers.ModelSerializer):

    class Meta:
        model = Payment
        fields = [
            'remain_price', 'tax_free', 'remain_tax_free',
            'cancelled_price', 'cancelled_tax_free',
            'requested_at', 'purchased_at', 'status'
        ]


class PaymentCancelSerialzier(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            'remain_price', 'remain_tax_free',
            'cancelled_price', 'cancelled_tax_free',
            'revoked_at', 'status'
        ]


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['name', 'phone', 'zipNo', 'Addr', 'detailAddr']


class AddressCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Address
        fields = ['user', 'name', 'phone', 'zipNo', 'Addr', 'detailAddr']


class TempAddressSerializer(serializers.ModelSerializer):
    name = serializers.NullBooleanField()
    zipNo = serializers.NullBooleanField()
    Addr = serializers.NullBooleanField()
    detailAddr = serializers.NullBooleanField()

    class Meta:
        model = User
        fields = ['name', 'phone', 'zipNo', 'Addr', 'detailAddr']


class UserNamePhoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['nickname', 'phone']
