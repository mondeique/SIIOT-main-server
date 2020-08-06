from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import authentication, mixins
from rest_framework.decorators import authentication_classes, action
from rest_framework import status, viewsets
from rest_framework import exceptions

from django.db.models import F, Sum, Q
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.db import transaction

from chat.models import ChatRoom
from transaction.models import Delivery, Transaction
from products.models import Product, ProductStatus
from .Bootpay import BootpayApi
# model
from .loader import load_credential
from .models import Payment, Trade, Deal, TradeErrorLog, PaymentErrorLog, Wallet
from payment.models import Commission

# serializer
from .serializers import (
    TradeSerializer,
    PayformSerializer,
    PaymentDoneSerialzier,
    PaymentCancelSerialzier,
    AddressSerializer, PaymentSerializer,
    TempAddressSerializer, AddressCreateSerializer, UserNamePhoneSerializer, PaymentConfirmSerializer)
from .utils import groupbyseller


def pay_test(request):
    return render(request, 'pay_test.html')


# Cart
class TradeViewSet(viewsets.GenericViewSet, mixins.DestroyModelMixin):
    queryset = Trade.objects.all().select_related('product', 'product_status') \
        .select_related('seller', 'seller__delivery_policy', 'seller__profile') \
        .select_related('buyer', 'buyer__address')
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]

    @action(methods=['put'], detail=True)
    def bagging(self, request, pk):
        """
        [DEPRECATED 2020.07.01] for 1차 출시
        장바구니 담은 api 입니다.
        api: PUT api/v1/trade/{id}/bagging/
        * id: product id

        :return 404 not found
                206 updated
        """
        buyer = request.user
        product = get_object_or_404(Product, pk=pk)
        Trade.objects.get_or_create(
            product=product,
            seller=product.seller,
            buyer=buyer,
        )
        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @action(methods=['get'], detail=False)
    def cart(self, request):
        """
        [DEPRECATED 2020.07.01] for 1차 출시
        카트 조회 api 입니다. return status 가 False 인 상품의 경우 판매완료 or 누군가가 구매중, 판매자가 수정 중 인 경우입니다.
        * 장바구니에서 각 상황에 따라 어떻게 보여줄지 구체적인 기획이 필요합니다.
        * 현재 : status 0: 구매가능, 1: 판매완료, 2: 다른 user 구매 중, 3: 판매자 수정 중
        api: GET api/v1/trade/cart/

        """
        buyer = request.user
        trades = self.get_queryset().filter(buyer=buyer, status=1)
        if trades.filter(product__sold=True).exists():
            trades.filter(product__sold=True).delete()
        serializer = TradeSerializer(trades, many=True)
        return Response(groupbyseller(serializer.data))

    @action(methods=['post'], detail=False)
    def cancel(self, request):
        """
        [DEPRECATED 2020.07.01] for 1차 출시
        장바구니 상품 삭제 api
        api: POST api/v1/trade/cancel/

        data: {trades: list(pk list)}
        """
        trades_id = request.data['trades']
        trades = self.get_queryset().filter(pk__in=trades_id, status=1)
        if trades.exists():
            trades.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def get_payform(self, request, *args, **kwargs):
        """
        [DEPRECATED] 장바구니에서 구매하기 클릭 시 호출되는 api (결제 폼 생성)
        [UPDATED] 상품 디테일 페이지에서 바로 결제 : 호출 시 product 에 해당하는 trade 생성
        api: POST api/v1/trade/get_payform/

        [DEPRECATED] data: {'trades': list(pk list)}
        [UPDATED]  data: {'product_id' : int}

        return
        * api 호출 시 구매 불가한 상태 : 판매완료인 경우 403 forbidden , 수정 중인 경우 406 not acceptable
        """
        buyer = request.user

        product_id = request.data['product_id']
        product = get_object_or_404(Product, pk=product_id)

        # check status
        p_status = product.status
        if p_status.sold:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if p_status.hiding:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        trade, _ = Trade.objects.get_or_create(
            product=product,
            seller=product.seller,
            buyer=buyer,
        )

        user_info = UserNamePhoneSerializer(buyer).data
        addresses = buyer.address.filter(recent=True)

        if addresses:
            addr = AddressSerializer(addresses.last()).data
        else:
            addr = TempAddressSerializer(buyer).data

        trade_serializer = TradeSerializer(trade)
        ordering_product = groupbyseller(trade_serializer.data)

        payinfo_data = ordering_product.copy()
        payinfo = payinfo_data.pop('payinfo')
        total_price = int(payinfo['total'])
        delivery_charge = int(payinfo['delivery_charge'])
        mountain_delivery_charge = int(payinfo['mountain_delivery_charge'])

        return Response(
            {"ordering_product": ordering_product,
             "user_info": user_info,
             "address": addr,
             "price": {"price": total_price,
                       "delivery_charge": delivery_charge,
                       "mountain_delivery_charge": mountain_delivery_charge,
                       }
             }
            , status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Trade.objects.all() \
        .select_related('product', 'product__status') \
        .select_related('seller', 'seller__delivery_policy')
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(PaymentViewSet, self).__init__(*args, **kwargs)
        self.serializer = None
        self.address = None
        self.payment = None
        self.user = None
        self.trades = None
        self.data = None
        self.trades_id = None

    @staticmethod
    def get_access_token():
        bootpay = BootpayApi(application_id=load_credential("application_id"),
                             private_key=load_credential("private_key"))
        result = bootpay.get_access_token()
        if result['status'] is 200:
            return bootpay
        else:
            raise exceptions.APIException(detail='bootpay access token 확인바람')

    def create(self, request, *args, **kwargs):
        """
        bootpay 결제 시작
        api: POST api/v1/payment/

        :param request: trade(pk list), price(total), address:obj(name, phone, zipNo, Addr, detailAddr), memo, mountain(bool), application_id(int)

        :return: result {payform}
        """
        data = request.data.copy()

        # test for web
        data = {"trade": [5], "price": 100,
                "address": {"name":"이름",
                            "phone": '01032423121',
                            "zipNo":'12345',
                            "Addr":'서울시 관악구',
                            "detailAddr": '302호'},
                "memo":'',
                "application_id" : 1}
        self.data = data
        self.request = request
        self.user = request.user

        # address 저장 후 str로 변환하여 deal 에서 사용
        self.address = data.pop('address', None)
        self.address_obj = self.save_address  # address instance
        address_str = self.address_obj.address
        data.update(address=address_str)

        self.serializer = self.get_serializer(data=data)
        self.serializer.is_valid(raise_exception=True)

        self.trades_id = self.serializer.validated_data['trade']
        self.trades = self.get_queryset().filter(pk__in=self.trades_id, buyer=request.user)

        self.check_trades()
        self.check_sold()

        # payment는 삭제하면 안됨
        with transaction.atomic():
            self.create_payment()
            self.create_deals()  # deal 생성과 동시에 상품 상태를 purchasing 으로 바꿈

        serializer = PayformSerializer(self.payment, context={
            'addr': self.serializer.validated_data['address'],
            'application_id': self.serializer.validated_data['application_id'],
            'items': self.trades
        })
        return Response({'results': serializer.data}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def confirm(self, request):
        """
        bootpay 결제 확인
        api: POST api/v1/payment/confirm/

        :param request: order_id(payment id와 동일), receipt_id(결제 영수증과 같은 개념:pg 사 발행)

        :return: code and status
        """
        serializer = PaymentConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = Payment.objects.get(pk=serializer.validated_data['order_id'])
        user = request.user

        if Product.objects.filter(trades__deal__payment=payment) \
                .filter(Q(status__sold=True)|
                        Q(status__purchasing=True)|
                        Q(status__editing=True)|
                        Q(status__hiding=True)).exists():

            # 구매할 수 없는 상태의 제품이 존재하므로, user의 trades, deal, transaction, payment를 삭제해야함
            product_ids = Product.objects.filter(trades__deal__payment=payment, sold=True).values_list('id', flat=True)

            deals = payment.deal_set.all()

            for deal in deals:
                deal.trades.all().delete()
                deal.delivery.delete()
            deals.delete()
            payment.delete()

            TradeErrorLog.objects.create(user=user, product_ids=list(product_ids), status=2,
                                         description="판매되었거나 구매중이거나 수정중인 제품이 있습니다.")
            raise exceptions.NotAcceptable(detail='판매된 제품이 포함되어 있습니다.')

        # payment : 결제 승인 전
        payment.receipt_id = serializer.validated_data['receipt_id']
        payment.status = 2
        payment.save()

        return Response(status=status.HTTP_200_OK)

    @transaction.atomic
    @action(methods=['post'], detail=False)
    def done(self, request):
        """
        bootpay 결제 완료시 호출되는 api 입니다.
        api: POST api/v1/payment/done/

        :param request: order_id(payment id와 동일), receipt_id(결제 영수증과 같은 개념:pg 사 발행)

        :return: status, code

        * receipt_id와 order_id로 payment를 못 찾을 시 payment와 trades의 status를 조정할 알고리즘 필요
        * front에서 제대로 값만 잘주면 문제될 것은 없지만,
        * https://docs.bootpay.co.kr/deep/submit 해당 링크를 보고 서버사이드 결제승인으로 바꿀 필요성 있음
        * https://github.com/bootpay/server_python/blob/master/lib/BootpayApi.py 맨 밑줄
        """
        receipt_id = request.data.get('receipt_id', None)
        order_id = request.data.get('order_id', None)
        if not (receipt_id or order_id):
            PaymentErrorLog.objects.create(user=request.user, temp_payment=request.user.payment_set.last(),
                                           description='잘못된 요청입니다. 결제는 되었으니 부트페이 확인 필요',
                                           bootpay_receipt_id=request.user.payment_set.last().receipt_id)
            raise exceptions.NotAcceptable(detail='request body is not validated')

        try:
            payment = Payment.objects.get(id=order_id)
        except Payment.DoesNotExist:
            # 이런 경우는 없겠지만, payment 를 찾지 못한다면, User의 마지막 생성된 payment로 생각하고 에러 로그 생성
            PaymentErrorLog.objects.create(user=request.user, temp_payment=request.user.payment_set.last(),
                                           description='해당 order_id의 payment가 존재하지 않습니다. 결제는 되었으니 부트페이 확인 필요',
                                           bootpay_receipt_id=receipt_id)
            raise exceptions.NotFound(detail='해당 order_id의 payment가 존재하지 않습니다.')

        # 결제 승인 중 (부트페이에선 결제 되었지만, done api 에서 처리 전)
        payment.status = 3
        payment.save()
        buyer = payment.user

        bootpay = self.get_access_token()
        result = bootpay.verify(receipt_id)
        if result['status'] == 200:
            # 성공!
            if payment.price == result['data']['price']:
                serializer = PaymentDoneSerialzier(payment, data=result['data'])
                if serializer.is_valid():
                    serializer.save()

                    # 관련 상품 sold처리
                    product_status = ProductStatus.objects.filter(product__trades__deal__payment=payment)
                    product_status.update(sold=True, purchasing=False, sold_status=1)

                    # 하위 trade 2번처리 : 결제완료
                    trades = Trade.objects.filter(deal__payment=payment)
                    trades.update(status=1)

                    # deal : 결제완료, 거래 시간 저장
                    payment.deal_set.update(status=2, transaction_completed_date=datetime.now())

                    # payment : 결제 완료
                    payment.status = 1
                    payment.save()

                    for deal in payment.deal_set.all():
                        # 판매 승인 모델 생성 : 각 상품 별로 판매 승인이 이루어집니다.
                        Transaction.objects.create(deal=deal, due_date=datetime.now()+timedelta(hours=12))
                        ChatRoom.objects.create(seller=deal.seller, buyer=deal.buyer, deal=deal)

                        # todo : 거래내역 확인 및 알림 처리
                        # reference = UserActivityReference.objects.create(deal=deal)
                        # activity log 생성 : seller
                        # UserActivityLog.objects.create(user=deal.seller, status=200, reference=reference)
                        # activity log 생성 : buyer
                        # UserActivityLog.objects.create(user=buyer, status=100, reference=reference)
                    return Response(status.HTTP_200_OK)
        else:
            # payment : 결제 승인 실패
            payment.status = -2
            payment.save()

            # bootpay 취소 요청
            result = bootpay.cancel(receipt_id, name='siiot', reason='시옷 서버 결제승인 실패로 인한 결제취소')
            serializer = PaymentCancelSerialzier(payment, data=result['data'])

            if serializer.is_valid():
                serializer.save()
                PaymentErrorLog.objects.create(user=request.user, temp_payment=payment, description='bootpay 결제 실패, 취소 완료')

                # trade : bootpay 환불 완료
                Trade.objects.filter(deal__payment=payment).update(status=-3)  # 결제되었다가 취소이므로 환불.

                # deal : bootpay 환불 완료
                payment.deal_set.all().update(status=-3)

                # payment : 결제 취소 완료
                payment.status = 20
                payment.save()

                for deal in payment.deal_set.all():
                    Transaction.objects.create(deal=deal, status=-2)

                # activity log : buyer 결제 취소됨
                # UserActivityLog.objects.create(user=buyer, status=190)

                return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)
            else:
                PaymentErrorLog.objects.create(user=request.user, temp_payment=payment,
                                               description='bootpay 결제 되었지만 서버에러. 부트페이 확인 후 처리 필요.',
                                               bootpay_receipt_id=receipt_id)
                for deal in payment.deal_set.all():
                    Transaction.objects.create(deal=deal, status=-1)

        return Response({'detail': ''}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def cancel(self, request):
        """
        결제 진행 취소 시 client 에서 호출하는 api 입니다.
        상품 상태를 초기화 합니다.
        # TODO : check 프로세스
        api: POST api/v1/payment/cancel/

        :param request: order_id(payment id와 동일)
        """
        payment = Payment.objects.get(pk=request.data.get('order_id'))

        ProductStatus.objects.filter(product__trade__deal__payment=payment).update(purchasing=False)
        return Response(status=status.HTTP_200_OK)  # hmm..

    @action(methods=['post'], detail=False)
    def error(self, request):
        """
        결제 중 에러 발생 시 client 에서 호출하는 api 입니다.
        상품 상태를 초기화 합니다.
        # TODO : check 프로세스

        api: POST api/v1/payment/error/

        :param request: order_id(payment id와 동일)
        """
        payment = Payment.objects.get(pk=request.data.get('order_id'))

        ProductStatus.objects.filter(product__trade__deal__payment=payment).update(purchasing=False)
        return Response(status=status.HTTP_200_OK)  # hmm..

    def create_payment(self):
        self.payment = Payment.objects.create(user=self.user)

    def check_trades(self):
        """
        request trades 가 유효한지 확인합니다.
        """
        if self.trades.exclude(buyer=self.user).exists():
            product_ids = Product.objects.filter(trades__in=self.trades).values_list('pk', flat=True)
            TradeErrorLog.objects.create(user=self.user, product_ids=product_ids, status=1,
                                         description="잘못된 trades id 로 요청하였습니다.")
            raise exceptions.NotAcceptable(detail='잘못된 정보로 요청하였습니다.')

    def check_total_price(self):
        """
        client 의 price 와 실제 data 상의 price 가 맞는지 check 합니다.
        * 결제 중 seller 가 상품의 가격을 수정하는 경우 에러가 발생합니다.
        """
        total_sum = self.payment.deal_set.aggregate(total_sum=Sum('total'))['total_sum']
        if total_sum != int(self.serializer.validated_data.get('price')):
            product_ids = Product.objects.filter(trades__in=self.trades).values_list('pk', flat=True)
            TradeErrorLog.objects.create(user=self.user, product_ids=product_ids, status=1,
                                         description="상품의 가격이 맞지 않습니다. 결제 중 셀러가 가격을 수정하였거나, 서버 확인이 필요합니다.")
            raise exceptions.NotAcceptable(detail='가격을 확인해주시길 바랍니다.')

    def check_sold(self):
        """
        구매 가능한 상품들인지 확인합니다.
        :return:
        """
        sold_products_trades = self.trades.filter(Q(product__status__sold=True)|
                                                  Q(product__status__purchasing=True)|
                                                  Q(product__status__editing=True)|
                                                  Q(product__status__hiding=True))

        if sold_products_trades.exists():
            product_ids = Product.objects.filter(trades__in=self.trades).values_list('pk', flat=True)
            # sold_products_trades.delete()  # 만약 결제된 상품이면, 카트(trades)에서 삭제해야함.
            TradeErrorLog.objects.create(user=self.user, product_ids=list(product_ids), status=1,
                                         description="판매되었거나 구매중이거나 수정중인 제품이 있습니다.")
            raise exceptions.NotAcceptable(detail='구매할 수 없는 상품이 있습니다.')

    def get_deal_total_and_delivery_charge(self, seller, trades):
        """
        [DEPRECATED] 셀러별로 묶인 trades 에서 총 금액, 정산금액, 배송비를 계산합니다.
        [UPDATED] 한번에 한개의 상품을 구매하는 것으로 변경
        """
        commission_rate = Commission.objects.last().rate  # admin에서 처리

        total_charge = trades.aggregate(total_charge=Sum(F('product__price')))['total_charge']
        if self.data.get('mountain', None):  # client 에서 도서산간 On 했을 때.
            delivery_charge = seller.delivery_policy.mountain
        elif trades.first().product.free_delivery:
            delivery_charge = 0
        else:
            delivery_charge = seller.delivery_policy.general  # 배송비 할인 없음.

        # return
        total = total_charge + delivery_charge,  # 총 결제 금액
        remain = total_charge * (1 - commission_rate) + delivery_charge,  # 정산 금액 : commission rate = 0
        total = int(total[0])
        remain = int(remain[0])
        return total, remain, delivery_charge

    def create_deals(self):
        """
        trades 를 셀러별로 묶어 deal 을 생성합니다.
        """
        bulk_list_delivery = []
        for seller_id in self.trades.values_list('seller', flat=True).distinct():  # 서로 다른 셀러들 결제시 한 셀러씩.

            trades_groupby_seller = self.trades.filter(seller_id=seller_id)  # 셀러 별로 묶기.
            seller = trades_groupby_seller.first().seller  # 셀러 인스턴스 가져오기.
            total, remain, delivery_charge = self.get_deal_total_and_delivery_charge(seller, trades_groupby_seller)

            deal = Deal.objects.create(
                buyer=self.user,
                seller=seller,
                total=total,
                remain=remain,
                delivery_charge=delivery_charge,
                payment=self.payment
            )

            bulk_list_delivery.append(Delivery(
                address=self.address_obj,
                memo=self.serializer.validated_data['memo'],
                mountain=self.serializer.validated_data['mountain'],
                state=Delivery._BEFORE_INPUT,
                deal=deal  # 유저가 결제시(한 셀러 샵에서 여러개 상품 구매시 하나의 delivery생성), 배송 정보 기입.
            ))

            trades_groupby_seller.update(deal=deal)  # deal 생성 후 trades instance update

        # check total sum for seller editing product price during purchasing
        self.check_total_price()
        self.payment.price = self.serializer.validated_data['price']

        if self.trades.count() > 1:
            self.payment.name = self.trades.first().product.name + ' 외 ' + str(self.trades.count() - 1) + '건'
        else:
            self.payment.name = self.trades.first().product.name

        self.payment.save()

        Delivery.objects.bulk_create(bulk_list_delivery)

    @property
    def save_address(self):
        """
        상품 구매 시 유저가 입력한 배송지 정보를 저장합니다. zipNo 로 이전에 같은 주소가 있으면 업데이트하고, 없으면 생성합니다.
        """
        address_data = self.address
        zip_no = address_data['zipNo']
        address_obj = self.user.address.filter(recent=True, zipNo=zip_no)

        if address_obj.exists():
            address_obj = address_obj.last()
            address_serializer = AddressCreateSerializer(address_obj, data=address_data, context={'request': self.request})
        else:
            address_serializer = AddressCreateSerializer(data=address_data, context={'request': self.request})

        address_serializer.is_valid(raise_exception=True)
        address = address_serializer.save()

        return address
