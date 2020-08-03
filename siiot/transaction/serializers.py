import datetime

from rest_framework import serializers

from core.utils import test_thumbnail_image_url
from crawler.models import CrawlProduct
from mypage.models import Address
from mypage.serializers import SimpleUserInfoSerializer
from payment.models import Deal
from products.models import Product
from transaction.models import Transaction, Delivery


class SimpleTransactionProductInfoSerializer(serializers.ModelSerializer):
    thumbnail_image_url = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['thumbnail_image_url', 'price', 'name', 'created_at']

    def get_thumbnail_image_url(self, obj):
        product = obj
        if not product.crawl_product_id:
            if hasattr(product, 'prodthumbnail'):
                return product.prodthumbnail.image_url
            # for develop
            try:
                return product.images.first().image_url
            except:
                return test_thumbnail_image_url
        return CrawlProduct.objects.get(id=product.crawl_product_id).thumbnail_image_url

    def get_created_at(self, obj):
        reformed_created_at = datetime.datetime.strftime(obj.created_at, '%y.%m.%d')
        return reformed_created_at


class SimpleTransactionPaymentInfoSerializer(serializers.ModelSerializer):
    total_product_price = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = ['total_product_price', 'delivery_charge', 'total']

    def get_total_product_price(self, deal):
        # 추후에는 product 의 가격들의 합으로
        # => total_price = deal.trades.aggregate(total_charge=Sum(F('product__price')))['total_charge']
        total_price = deal.total - deal.delivery_charge
        return total_price


class SimpleTransactionPaymentTimeSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    canceled_at = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['created_at', 'canceled_at']

    def get_created_at(self, obj):
        created_at = obj.created_at
        reformat_created_at = datetime.datetime.strftime(created_at, '%Y.%m.%d.%H:%M')
        return reformat_created_at

    def get_canceled_at(self, obj):
        canceled_at = obj.canceled_at
        if not canceled_at:
            return None
        reformat_canceled_at = datetime.datetime.strftime(canceled_at, '%Y.%m.%d.%H:%M')
        return reformat_canceled_at


class SimpleTransactionAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['name', 'phone', 'address']


class SimpleTransactionTransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = ['code', 'number']


class TransactionDetailSerializer(serializers.ModelSerializer):  # 공용
    products = serializers.SerializerMethodField()
    payment_info = serializers.SerializerMethodField()
    payment_time = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()
    transport = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = ['id',
                  'products',
                  'payment_info',
                  'payment_time',
                  'address',
                  'transport',
                  'status'
                  ]

    def get_products(self, transaction_obj):
        self.deal = transaction_obj.deal
        product = Product.objects.filter(trades__deal__transaction=transaction_obj)
        serializer = SimpleTransactionProductInfoSerializer(product, many=True)
        return serializer.data

    def get_info(self):
        payment = self.deal.payment
        serializer = SimpleTransactionPaymentInfoSerializer(payment)
        return serializer.data

    def get_payment_time(self, transaction_obj):
        serializer = SimpleTransactionPaymentTimeSerializer(transaction_obj)
        return serializer.data

    def get_address(self):
        address = self.deal.dealivery.address
        serializer = SimpleTransactionAddressSerializer(address)
        return serializer.data

    def get_transport(self):
        delivery = self.deal.dealivery
        if not delivery.number:
            return None
        serializer = SimpleTransactionTransportSerializer(delivery)
        return serializer.data


class SellerTransactionDetailSerializer(TransactionDetailSerializer):
    cancel_btn_active = serializers.SerializerMethodField()
    other_party = serializers.SerializerMethodField()

    class Meta(TransactionDetailSerializer.Meta):
        fields = TransactionDetailSerializer.Meta.fields + ['cancel_btn_active', 'other_party']

    def get_cancel_btn_active(self, transaction_obj):
        # 판매자 거래취소 버튼 활성화 : 판매승인, 운송장 번호 입력 후 까지는 거래취소 가능
        status = transaction_obj.status
        if status in [2, 3]:
            return True
        return False

    def get_other_party(self):
        buyer = self.deal.buyer
        serializer = SimpleUserInfoSerializer(buyer)
        return serializer.data


class BuyerTransactionDetailSerializer(TransactionDetailSerializer):
    cancel_btn_active = serializers.SerializerMethodField()
    other_party = serializers.SerializerMethodField()

    class Meta(TransactionDetailSerializer.Meta):
        fields = TransactionDetailSerializer.Meta.fields + ['cancel_btn_active', 'other_party']

    def get_cancel_btn_active(self, transaction_obj):
        # 구매자 거래취소 버튼 활성화 : 결제취소시, 구매확정시 제외하고는 거래취소 버튼 존재.
        # 이때, check cancel 호출 하여 pop up 띄움.
        status = transaction_obj.status
        if status in [-1, -2, -3, 5]:
            return False
        return True

    def get_other_party(self):
        seller = self.deal.seller
        serializer = SimpleUserInfoSerializer(seller)
        return serializer.data