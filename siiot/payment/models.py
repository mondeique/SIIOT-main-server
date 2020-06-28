import os
from datetime import timedelta, datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings

from products.models import Product


class Commission(models.Model):
    rate = models.FloatField(verbose_name='수수료', validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    info = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Payment(models.Model):
    """
    유저 결제시 생성되는 모델입니다.
    여러개의 상품을 한번에 결제하면 하나의 Payment obj 가 생성됩니다.
    """
    STATUS = [
        (0, '결제대기'),
        (1, '결제완료'),
        (2, '결제승인전'),
        (3, '결제승인중'),
        (20, '결제취소'),
        (-20, '결제취소실패'),
        (-30, '결제취소진행중'),
        (-1, '오류로 인한 결제실패'),
        (-2, '결제승인실패')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='유저')
    receipt_id = models.CharField(max_length=100, verbose_name='영수증키', db_index=True)
    status = models.IntegerField(choices=STATUS, verbose_name='결제상태', default=0)

    price = models.IntegerField(verbose_name='결제금액', null=True)
    name = models.CharField(max_length=100, verbose_name='대표상품명')

    # bootpay data
    tax_free = models.IntegerField(verbose_name='면세금액', null=True)
    remain_price = models.IntegerField(verbose_name='남은금액', null=True)
    remain_tax_free = models.IntegerField(verbose_name='남은면세금액',null=True)
    cancelled_price = models.IntegerField(verbose_name='취소금액', null=True)
    cancelled_tax_free = models.IntegerField(verbose_name='취소면세금액', null=True)
    pg = models.TextField(default='inicis', verbose_name='pg사')
    method = models.TextField(verbose_name='결제수단')
    payment_data = models.TextField(verbose_name='raw데이터')
    requested_at = models.DateTimeField(blank=True, null=True)
    purchased_at = models.DateTimeField(blank=True, null=True)
    revoked_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        if self.name:
            return self.name
        else:
            return


class Deal(models.Model):  # 돈 관련 (스토어 별로)
    """
    셀러별 한번에 결제를 구현하기 위해 만들었습니다.

    """

    STATUS = [
        (1, '결제시작'),  # get_payform
        (12, '결제확인'),  # confirm
        (13, '부트페이 결제완료'),  # done 진입 시
        (2, '결제완료'),  # payment/done/ 처리시 바뀜 = 배송전 , noti 날려주기.
        (3, '판매승인'),  # seller 승인시, 이 전에 결제 취소 가능, 이 이후에는 결제취소 요청
        (4, '운송장입력완료'),  # 운송장번호 입력시 바꿔줌. 배송중과 동일한 상태
        (5, '거래완료'),  # 셀러한테 noti 날려주기. // 리뷰남겼을떄, 판매승인 7일 후 (자동구매확정)
        (6, '정산완료'),  # 정산처리 후 admin 필요
        (-1, '결제취소신청'),  # 배송준비중인 상태에서 취소요청
        (-2, '결제취소'),  # 결제취소/ 결제취소요청 승인
        (-3, '결제취소완료'),  # bootpay 에서 결제 취소시
        (-20, '기타처리'),
    ]

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='Deal_seller')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='Deal_buyer')

    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    total = models.IntegerField(verbose_name='결제금액')
    remain = models.IntegerField(verbose_name='잔여금(정산금액)')  # 수수료계산이후 정산 금액., 정산이후는 0원, 환불시 감소 등.
    delivery_charge = models.IntegerField(verbose_name='배송비(참고)')
    status = models.IntegerField(choices=STATUS, default=1, db_index=True)
    is_settled = models.BooleanField(default=False, help_text="정산 여부(신중히 다뤄야 함)", verbose_name="정산여부(신중히)")

    transaction_completed_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def settable(self):
        """
        정산 가능 여부 , 거래 완료 여부
        """
        if self.status == 5:
            return True
        elif self.status in [2, 3, 4] and self.delivery.number_created_time:
            if self.delivery.number_created_time + timedelta(days=5) < datetime.now():
                return True
            else:
                return False
        else:
            return False

    # def save(self, *args, **kwargs):
    #     super(Deal, self).save(*args, **kwargs)


class Trade(models.Model):  # 카트, 상품 하나하나당 아이디 1개씩
    """
    장바구니 기능 및 결제시 각 상품에 대해 관리하기 위해 만들었습니다.
    추후 부분 결제 취소시 해당 obj 의 상태를 변경하면 됩니다.
    TODO: STATUS 변경
    """
    STATUS = [
        (1, '결제전'),
        (2, '결제완료'),  # payment/done/ 처리시 바뀜 = 배송전 , noti 날려주기.
        (3, '판매승인'),
        (4, '운송장입력'),   # 운송장번호 입력시 바꿔줌
        (5, '거래완료'),  # 셀러한테 noti 날려주기. // 리뷰남겼을떄, 판매승인 7일 후 (자동구매확정)
        (6, '정산완료'),  # 정산처리 후 admin 필요
        (-1, '결제취소신청'),  # 배송준비중인 상태에서 취소요청
        (-2, '결제취소'),  # 결제취소/ 결제취소요청 승인
        (-3, '결제취소완료'),  # bootpay 에서 결제 취소시
        (-20, '기타처리'),
    ]

    deal = models.ForeignKey(Deal, blank=True, null=True, on_delete=models.SET_NULL)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='Trade_seller')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='Trade_buyer')
    status = models.IntegerField(choices=STATUS, default=1)
    created_at = models.DateTimeField(auto_now_add=True, help_text="카트 담긴 시각")
    updated_at = models.DateTimeField(auto_now=True, help_text="카트 수정 시각")
    # todo: status : 결제, 배송, success, refund

    # @property
    # def settable(self):
    #     """
    #     정산 가능 여부 , 거래 완료 여부
    #     """
    #     deal = self.deal
    #     if not hasattr(deal, 'delivery'):
    #         print('asdasd')
    #     else:
    #         completed_date = deal.delivery.number_created_time
    #     if self.status == 5:
    #         return True
    #     elif self.status in [2, 3, 4] and completed_date:
    #         if completed_date + timedelta(days=5) < datetime.now():
    #             return True
    #         else:
    #             return False
    #     else:
    #         return False


class TradeLog(models.Model):
    STATUS = [
        (1, '결제전'),
        (2, '결제완료'),  # payment/done/ 처리시 바뀜 = 배송전 , noti 날려주기.
        (3, '배송중'),  # 운송장번호 입력시 바꿔줌
        (4, '배송완료'),
        (5, '거래완료'),  # 셀러한테 noti 날려주기. // 리뷰남겼을떄, 판매승인 7일 후 (자동구매확정)
        (6, '정산완료'),  # 정산처리 후 admin 필요
        (-1, '환불신청'),
        (-2, '환불승인'),
        (-3, '환불완료'),
        (-20, '환불반려'),
    ]

    trade = models.ForeignKey(Trade, on_delete=models.CASCADE)
    log = models.TextField()
    status = models.IntegerField(choices=STATUS)
    created_at = models.DateTimeField(auto_now_add=True)


class TradeErrorLog(models.Model):
    """
    상품 결제 시 에러 로그 저장.
    """
    STATUS = [
        (1, 'payform'),
        (2, 'confirm'),
        (3, 'done'),
        (0, 'other'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    product_ids = models.TextField()
    status = models.IntegerField(choices=STATUS)
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class PaymentErrorLog(models.Model):
    """
    부트페이에선 결제가 되었지만, done api 호출 시 에러가 나, 서버상에선 결제 완료 처리가 되지 않았을 경우 환불 or 결제 완료
    처리해야 하기 때문에 로그 생성
    """

    # TODO : statelessful 하지 않도록 server side 렌더링이 필요
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    temp_payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL)
    description = models.CharField(max_length=100)


class WalletLog(models.Model):
    """
    정산을 수행하는 모델입니다.
    """
    STATUS = [
        (1, '정산대기'),
        (2, '정산완료'),
        (-3, '환불처리'),
        (99, '기타')
    ]
    status = models.IntegerField(choices=STATUS, default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    amount = models.IntegerField(help_text="정산금액", default=0)
    log = models.TextField(verbose_name='로그 및 특이사항')
    deal = models.OneToOneField(Deal, blank=True, null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_settled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "정산 관리"
        verbose_name_plural = "정산 관리"

    def save(self, *args, **kwargs):
        # self._check_deal_status()
        super(WalletLog, self).save(*args, **kwargs)

    # def _check_deal_status(self):
    #     from user_activity.models import UserActivityReference, UserActivityLog
    #
    #     if self.is_settled:
    #         deal = self.deal
    #         if deal.status == 6 or deal.is_settled:
    #             raise Exception('정산이 불가한 상태입니다.')
    #         elif deal.settable:
    #
    #             # activity 생성을 위함
    #             reference = UserActivityReference.objects.get_or_create(deal=deal)
    #             print(reference)
    #             self.status = 2
    #             self.deal.is_settled = True
    #             self.deal.save()
    #
    #             # 정산 완료시 알림
    #             UserActivityLog.objects.get_or_create(user=deal.seller, status=203, reference=reference)
    #
    #         else:
    #             raise Exception('정산이 불가한 상태입니다.')
