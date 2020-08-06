from datetime import datetime

from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, action
from rest_framework import status, viewsets
from rest_framework import exceptions

from reviews.models import Review
from transaction.models import Transaction
from payment.Bootpay import BootpayApi
from payment.loader import load_credential
from payment.models import Deal
from payment.serializers import PaymentCancelSerialzier


class TransactionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = None
    queryset = Transaction.objects\
                            .filter(deal__trades__product__status__sold=True, deal__trades__product__status__sold_status=1)
    """
    구매자 결제 이후 구매 취소, 판매 거절, 판매 승인, 구매 확정 등 결제이후 행동에 관련된 api 입니다.
    추후 한번에 결제 구현을 위해 Deal 별로 거래 취소 단위를 묶는게 아닌, Trade 단위로 동작합니다.
    """

    def __init__(self, *args, **kwargs):
        super(TransactionViewSet, self).__init__(*args, **kwargs)
        self.trade = None
        self.payment = None
        self.receipt_id = None
        self.wallet = None
        self.deal = None
        self.cancel_requester = None
        self.cancel_reason = ''
        self.transaction = None

    @staticmethod
    def get_access_token():
        bootpay = BootpayApi(application_id=load_credential("application_id"),
                             private_key=load_credential("private_key"))
        result = bootpay.get_access_token()
        if result['status'] is 200:
            return bootpay
        else:
            raise exceptions.APIException(detail='bootpay access token 확인바람')


    @transaction.atomic
    @action(methods=['put'], detail=True)
    def cancel(self, request, *args, **kwargs):
        """
        구매자, 판매자의 거래취소 입니다. 각각 reason을 받아야 합니다.
        취소 후에 판매 중으로 상태를 변경합니다.
        TODO : post save로 알림 내역 저장. 알림 내역 저장하면서 푸쉬 알림
        """

        user = request.user
        transaction_obj = self.get_object()
        deal = transaction_obj.deal

        if transaction_obj.status in [-1, -2, -3]:  # 이미 거래취소 완료
            return Response({'error_message': '거래가 취소된 상품입니다.'}, status=status.HTTP_403_FORBIDDEN)

        if deal.seller == user:
            if transaction_obj.seller_accepted is None:  # 판매 승인, 거절을 하지 않은 경우
                return Response({'error_message': '판매승인 또는 판매거절을 해주세요'}, status=status.HTTP_403_FORBIDDEN)
            if transaction_obj.status == 5:
                return Response({'error_message': '거래가 완료된 상품입니다.'}, status=status.HTTP_403_FORBIDDEN)

        elif deal.buyer == user:
            if transaction_obj.status == 2:  # 판매승인 => 배송중비중
                return Response({'error_message': '배송준비중인 상품입니다. 판매자에게 문의해주세요'}, status=status.HTTP_403_FORBIDDEN)
            if transaction_obj.status == 3:  # 배송중 => 운송장 입력 됨
                return Response({'error_message': '배송중인 상품입니다. 판매자에게 문의해주세요'}, status=status.HTTP_403_FORBIDDEN)
            if transaction_obj.status == 5:  # 거래완료 => 구매확정 또는 자동구매확정
                return Response({'error_message': '거래가 완료된 상품입니다.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        buyer_cancel_reason = data.get('reason', None)
        seller_cancel_reason = data.get('reason', None)

        if self.deal.seller == user:
            if not seller_cancel_reason:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            transaction_obj.seller_cancel = True
            transaction_obj.seller_cancel_reason = seller_cancel_reason
            self.cancel_requester = user
            self.cancel_reason = '판매자 요청으로 인한 거래취소'

        if self.deal.buyer == user:
            if not buyer_cancel_reason:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            transaction_obj.buyer_cancel = True
            transaction_obj.buyer_cancel_reason = buyer_cancel_reason
            self.cancel_requester = user
            self.cancel_reason = '구매자 요청으로 인한 거래취소'

        transaction_obj.status = -2
        transaction_obj.save()
        self.transaction = transaction_obj

        # 거래취소이므로 다시 판매중으로 등록
        for product in self.deal.trades.all():
            p_status = product.status
            p_status.sold = False
            p_status.sold_status = None
            p_status.save()

        self.payment = self.deal.payment
        self.receipt_id = self.payment.receipt_id

        self._payment_cancel_status()

        return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(methods=['put'], detail=True)
    def reject(self, request, *args, **kwargs):
        """
        판매자 판매 거절 : 판매 거절 사유를 입력받아야 합니다.
        거절 후에도 판매 완료인 상태로 유지합니다.
        """
        data = request.data.copy()
        seller_reject_reason = data.get('reason', None)

        if not seller_reject_reason:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        transaction_obj = self.get_object()
        self.deal = transaction_obj.deal

        # 판매자가 아니면 403
        if self.deal.seller != user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # 판매 거절 업데이트
        transaction_obj.seller_accepted = False
        transaction_obj.seller_reject_reason = seller_reject_reason
        transaction_obj.status = -2
        transaction_obj.save()
        self.transaction = transaction_obj

        # 판매거절 이후 판매자가 알아서 판매완료 처리
        for product in self.deal.trades.all():
            p_status = product.status
            p_status.sold = False
            p_status.sold_status = None
            p_status.save()

        self.cancel_requester = user
        self.cancel_reason = '판매자 요청으로 인한 판매거절 (판매할 수 없는 상태일 때)'

        self.payment = self.deal.payment
        self.receipt_id = self.payment.receipt_id

        self._payment_cancel_status()

        return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)

    def _payment_cancel_status(self):
        bootpay = self.get_access_token()
        result = bootpay.cancel(self.receipt_id, name=self.cancel_requester, reason=self.cancel_reason)
        serializer = PaymentCancelSerialzier(self.payment, data=result['data'])

        if serializer.is_valid():
            serializer.save()

            # deal : 결제 취소
            self.deal.status = -2
            self.deal.save()

            # payment : 결제 취소 완료 : 한번에 하나 결제이기 떄문에
            self.payment.status = 20
            self.payment.save()

            # transaction : 결제 취소 시각 저장
            self.transaction.canceled_at = datetime.now()
            self.transaction.save()

            for trade in self.deal.trades.all():
                trade.status = 2
                trade.save()

        else:
            raise exceptions.ValidationError(detail='취소 과정에서 오류가 발생했습니다.')

    @transaction.atomic
    @action(methods=['put'], detail=True)
    def approval(self, request, *args, **kwargs):
        """
        판매자 판매 승인
        """
        user = request.user
        transaction_obj = self.get_object()
        deal = transaction_obj.deal

        if deal.seller != user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        transaction_obj = deal.transaction
        transaction_obj.seller_accepted = True
        transaction_obj.status = 2
        transaction_obj.save()

        return Response(status=status.HTTP_201_CREATED)

    @transaction.atomic
    @action(methods=['put'], detail=True)
    def confirm(self, request, *args, **kwargs):
        """
        구매자 구매 확정 : 구매 확정시 정산 내역에 정산 예정일이 업데이트 됩니다.
        # TODO : cron 자동 구매확정
        """
        user = request.user
        transaction_obj = self.get_object()
        deal = transaction_obj.deal

        if deal.buyer != user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        transaction_obj = deal.transaction
        transaction_obj.confirm_transaction = True
        transaction_obj.status = 5
        transaction_obj.save()  # create wallet

        return Response(status=status.HTTP_200_OK)

    @action(methods=['put'], detail=True)
    def review(self, request, *args, **kwargs):
        """
        # TODO : POST 로 할 것이냐, PUT 으로 할 것이냐..
        # TODO : PUT 으로 한 경우, 서버 리소스 많이 듦 => serializer 쓰기 어려움.
        # TODO : POST 로 한 경우, serializer 사용 가능. 하지만 모든 데이터를 주어야 함.
        """
        transaction_obj = self.get_object()
        deal = transaction_obj.deal
        user = request.user
        data = request.data.copy()
        satisfaction = data.get('satisfaction', None)

        if not satisfaction:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 구매자만 리뷰 남기기 가능
        if deal.buyer != user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        Review.objects.create(seller=deal.seller, buyer=user, deal=deal, satisfaction=satisfaction)

        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    def partial_cancel(self, request, *args, **kwargs):
        pass

    def partial_reject(self, request, *args, **kwargs):
        pass
