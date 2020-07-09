from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.decorators import authentication_classes, action
from rest_framework import status, viewsets
from rest_framework import exceptions

from core.utils import get_wallet_scheduled_date
from transaction.models import Transaction
from payment.Bootpay import BootpayApi
from payment.loader import load_credential
from payment.models import Deal
from payment.serializers import PaymentCancelSerialzier


class TransactionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ]
    serializer_class = None
    queryset = Deal.objects.filter(trades__product__status__sold=True, trades__product__status__sold_status=1) \
        .select_related('trades',
                        'trades__product',
                        'seller',
                        'buyer',
                        'payment',
                        'transaction')
    """
    구매자 결제 이후 구매 취소, 판매 거절, 판매 승인, 구매 확정 등 결제이후 행동에 관련된 api 입니다.
    추후 한번에 결제 구현을 위해 Deal 별로 거래 취소 단위를 묶는게 아닌, Trade 단위로 동작합니다.
    """

    def __init__(self):
        super(TransactionViewSet, self).__init__()
        self.trade = None
        self.payment = None
        self.receipt_id = None
        self.wallet = None
        self.deal = None

    @staticmethod
    def get_access_token():
        bootpay = BootpayApi(application_id=load_credential("application_id"),
                             private_key=load_credential("private_key"))
        result = bootpay.get_access_token()
        if result['status'] is 200:
            return bootpay
        else:
            raise exceptions.APIException(detail='bootpay access token 확인바람')

    @action(methods=['get'], detail=True)
    def cancel_check(self, request, *args, **kwargs):
        """
        거래 취소 버튼을 누를 때 호출되며, 거래취소가 가능한지 확인합니다.
        """
        user =request.user
        deal = self.get_object()
        transaction_obj = deal.transaction

        if transaction_obj.status in [-1, -2, -3]:  # 이미 거래취소 완료
            return Response({'error_code': '거래가 취소된 상품입니다.'}, status=status.HTTP_403_FORBIDDEN)

        if deal.seller == user:
            if transaction_obj.seller_accepted is None:  # 판매 승인, 거절을 하지 않은 경우
                return Response({'error_code': '판매승인 또는 판매거절을 해주세요'}, status=status.HTTP_403_FORBIDDEN)
            if transaction_obj.status == 5:
                return Response({'error_code': '거래가 완료된 상품입니다.'}, status=status.HTTP_403_FORBIDDEN)

        elif deal.buyer == user:
            if transaction_obj.status == 2:  # 판매승인 => 배송중비중
                return Response({'error_code': '배송준비중인 상품입니다. 판매자에게 문의해주세요'}, status=status.HTTP_403_FORBIDDEN)
            if transaction_obj.status == 3:  # 배송중 => 운송장 입력 됨
                return Response({'error_code': '배송중인 상품입니다. 판매자에게 문의해주세요'}, status=status.HTTP_403_FORBIDDEN)
            if transaction_obj.status == 5:  # 거래완료 => 구매확정 또는 자동구매확정
                return Response({'error_code': '거래가 완료된 상품입니다.'}, status=status.HTTP_403_FORBIDDEN)

        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


    @transaction.atomic
    @action(methods=['post'], detail=True)
    def cancel(self, request, *args, **kwargs):
        """
        구매자, 판매자의 거래취소 입니다. 각각 reason을 받아야 합니다.
        TODO : post save로 알림 내역 저장. 알림 내역 저장하면서 푸쉬 알림
        """
        user = request.user
        self.deal = self.get_object()
        data = request.data.copy()
        buyer_cancel_reason = data.get('reason', None)
        seller_cancel_reason = data.get('reason', None)
        transaction_obj = self.deal.transaction

        if self.deal.seller == user:
            if not seller_cancel_reason:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            transaction_obj.seller_cancel = True
            transaction_obj.seller_cancel_reason = seller_cancel_reason

        if self.deal.buyer == user:
            if not buyer_cancel_reason:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            transaction_obj.buyer_cancel = True
            transaction_obj.buyer_cancel_reason = buyer_cancel_reason

        transaction_obj.status = -2
        transaction_obj.save()

        self.payment = self.deal.payment
        self.receipt_id = self.payment.receipt_id

        self._payment_cancel_status()

        return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(methods=['post'], detail=True)
    def reject(self, request, *args, **kwargs):
        """
        판매자 판매 거절 : 판매 거절 사유를 입력받아야 합니다.
        """
        data = request.data.copy()
        seller_reject_reason = data.get('reason', None)

        if not seller_reject_reason:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        self.deal = self.get_object()

        # 판매자가 아니면 406
        if self.deal.seller != user:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        # 판매 거절 업데이트
        Transaction.objects.filter(deal=self.deal)\
            .update(seller_accepted=False, seller_reject_reason=seller_reject_reason, status=-2)

        self.payment = self.deal.payment
        self.receipt_id = self.payment.receipt_id

        self._payment_cancel_status()

        return Response({'detail': 'canceled'}, status=status.HTTP_200_OK)

    def _payment_cancel_status(self):
        bootpay = self.get_access_token()
        result = bootpay.cancel(self.receipt_id)
        serializer = PaymentCancelSerialzier(self.payment, data=result['data'])

        if serializer.is_valid():
            serializer.save()

            # deal : 결제 취소
            self.deal.status = -2
            self.deal.save()

            # payment : 결제 취소 완료 : 한번에 하나 결제이기 떄문에
            self.payment.status = 20
            self.payment.save()

            for trade in self.deal.trades.all():
                trade.status = 2
                trade.save()

        else:
            raise exceptions.ValidationError(detail='취소 과정에서 오류가 발생했습니다.')

    @transaction.atomic
    @action(methods=['post'], detail=True)
    def approval(self, request, *args, **kwargs):
        """
        판매자 판매 승인
        """
        user = request.user
        deal = self.get_object()

        if deal.seller != user:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        transaction_obj = deal.transaction
        transaction_obj.seller_accepted = True
        transaction_obj.status = 2
        transaction_obj.save()

        return Response(status=status.HTTP_201_CREATED)

    @transaction.atomic
    @action(methods=['post'], detail=True)
    def confirm(self, request, *args, **kwargs):
        """
        구매자 구매 확정 : 구매 확정시 정산 내역에 정산 예정일이 업데이트 됩니다.
        # TODO : cron 자동 구매확정
        """
        user = request.user
        deal = self.get_object()

        if deal.seller != user:
            return Response(status=status.HTTP_406_NOT_ACCEPTABLE)

        transaction_obj = deal.transaction
        transaction_obj.confirm_transaction = True
        transaction_obj.status = 5
        transaction_obj.save()

        wallet_date = get_wallet_scheduled_date()
        deal.wallet.scheduled_date = wallet_date
        deal.wallet.save()

        return Response(status=status.HTTP_200_OK)

    def partial_cancel(self, request, *args, **kwargs):
        pass

    def partial_reject(self, request, *args, **kwargs):
        pass
