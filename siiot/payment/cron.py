from datetime import datetime, time

from rest_framework import exceptions
from .Bootpay import BootpayApi
from .loader import load_credential
from .serializers import PaymentCancelSerialzier

from transaction.models import Transaction


def time_diff_in_s(start, end):
    duration_in_s = (end - start).seconds
    return duration_in_s


def get_access_token():
    bootpay = BootpayApi(application_id=load_credential("application_id"),
                         private_key=load_credential("private_key"))
    result = bootpay.get_access_token()
    if result['status'] is 200:
        return bootpay
    else:
        raise exceptions.APIException(detail='bootpay access token 확인바람')


def check_approval_after_payment():
    queryset = Transaction.objects.filter(status=1)
    # TODO: Transaction field 를 계속해서 변경하는 method or method below..
    for transaction_obj in queryset.iterator():
        if time_diff_in_s(transaction_obj.created_at, datetime.now()) > (3600 * 12):
            print("AUTO PAYMENT CANCEL : %d".format(transaction_obj.id))

            deal = transaction_obj.deal
            payment = deal.payment
            receipt_id = payment.receipt_id
            user = deal.buyer
            bootpay = get_access_token()
            result = bootpay.cancel(receipt_id, name=user, reason='결제 후 12시간이 지나 판매자 자동거래 취소')
            serializer = PaymentCancelSerialzier(payment, data=result['data'])

            if serializer.is_valid():
                serializer.save()

                # deal : 결제 취소
                deal.status = -2
                deal.save()

                # payment : 결제 취소 완료 : 한번에 하나 결제이기 떄문에
                payment.status = 20
                payment.save()

                # transaction : 결제 취소 시각 저장 및 자동결제취소 status 변경
                transaction_obj.canceled_at = datetime.now()
                transaction_obj.status = -3
                transaction_obj.save()

                # trade : 결제 취소
                for trade in deal.trades.all():
                    trade.status = 2
                    trade.save()

                # 자동취소 이후 상품 판매 중으로 처리
                for product in deal.trades.all():
                    p_status = product.status
                    p_status.sold = False
                    p_status.sold_status = None
                    p_status.save()

            else:
                raise exceptions.ValidationError(detail='취소 과정에서 오류가 발생했습니다.')
        else:
            pass