from datetime import timedelta, datetime

from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.db import models
from django.conf import settings
from django.db.models import Sum

from core.utils import get_wallet_scheduled_date
from mypage.models import Address
from payment.models import Deal, Trade, Wallet

"""
배송 전반적인 프로세스를 다룹니다.
판매승인, 운송장 입력, 배송 정보 등을 다룹니다.
"""


class Transaction(models.Model):
    """
    판매자가 판매 승인, 구매자가 구매 취소에 사용하는 모델입니다.
    판매자 승인이 되어야 구매자의 주소확인이 가능하고, 채팅방이 생성됩니다.
    # TODO : post save로 알림 내역 저장. 알림 내역 저장하면서 푸쉬 알림
    """
    STATUS = [
        (1, '결제완료'),
        (2, '배송준비'),
        (3, '배송완료'),
        (4, '거래완료'),
        (-1, '오류로 인한 결제실패'),
        (-2, '거래취소'),
        (-3, '자동거래취소')
    ]
    deal = models.OneToOneField(Deal, related_name='transaction', on_delete=models.CASCADE)

    status = models.IntegerField(choices=STATUS, default=1)

    seller_accepted = models.NullBooleanField(help_text="승인 또는 거절을 위한 필드입니다. default=null")
    seller_reject_reason = models.CharField(null=True, blank=True, max_length=100, help_text='판매 거절 사유입니다. 구매자에게 전달됩니다.')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    due_date = models.DateTimeField(help_text="유효 시간입니다. created_at + 12h로 자동생성 됩니다."
                                              "유효시간이 지날 경우 cron 에서 체크하여 구매 취소 처리 합니다.")

    buyer_cancel = models.NullBooleanField(help_text='구매자가 구매 취소를 위한 필드입니다.')
    buyer_cancel_reason = models.CharField(null=True, blank=True, max_length=100, help_text='구매 취소 사유입니다. 판매자에게 전달됩니다.')

    confirm_transaction = models.NullBooleanField(help_text='구매확정 필드입니다. True 로 변환 시 Wallet을 생성합니다.')

    @property
    def checker(self):
        """
        판매자가 accepted 할 수 있는 condition 인지 확인합니다.
        view 에서 이를 참고하여 is_accepted 의 status 을 처리합니다.
        """
        now = datetime.now()
        diff = now - self.due_date
        if self.seller_accepted is None and diff <= timedelta(0):
            return True
        return False

    @property
    def cron_checker(self):
        """
        deal 생성 이후 12h 이내 승인이 이루어졌는지 check 하는 property 입니다.
        만약 12h 이내 생성되지 않았다면, 매 시간마다 도는 cron으로 구매 취소 처리 합니다.
        """
        now = datetime.now()
        diff = now - self.due_date
        if self.seller_accepted or diff <= timedelta(0):
            return True
        return False

    def save(self, *args, **kwargs):
        super(Transaction, self).save(*args, **kwargs)
        self._create_wallet()

    def _create_wallet(self):
        if self.confirm_transaction:
            amount = self.deal.trades.filter(status=1).aggregate(price=Sum('product__price'))['price']
            date = get_wallet_scheduled_date()
            Wallet.objects.create(deal=self.deal, seller=self.deal.seller, amount=amount, scheduled_date=date)


class TransactionPartialCancelLog(models.Model):
    """
    각 상품별 구매취소, 판매 취소시 생성되는 log 모델입니다. 생성 시 Trade 상태를 구매취소로 변환합니다.
    1차 출시에는 판매승인 이전에만 구매취소 할 수 있고, 판매승인 이후에는 구매취소가 불가능합니다.
    """
    trade = models.ForeignKey(Trade, related_name='cancel', on_delete=models.CASCADE)
    transaction = models.ForeignKey(Transaction, related_name='partial_cancels', on_delete=models.CASCADE)

    seller_reject_reason = models.CharField(null=True, blank=True, max_length=100)
    buyer_reject_reason = models.CharField(null=True, blank=True, max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def cancel_product_name(self):
        product = self.trade.product
        return '[결제취소] {}'.format(product.name)

    def save(self, *args, **kwargs):
        self.trade.status = -2
        self.trade.save()  # status=-2 결제취소
        super(TransactionPartialCancelLog, self).save(*args, **kwargs)


class Delivery(models.Model):
    """
    배송 관련 모델입니다. 판매 승인시 생성되며, 운송장 번호를 입력받는 모델입니다.
    deal 과 1:1 관계이며, address 를 참고합니다.
    deal 과 payment 는 삭제되면 안됩니다!
    """

    _BEFORE_INPUT = 1
    _COMPLETE_INPUT = 2
    _TAKE_PRODUCT = 3
    _MOVING = 4
    _ARRIVAL_HUB = 5
    _ON_DELIVER = 6
    _ARRIVAL = 7

    states = [
        (_BEFORE_INPUT, '운송장입력전'),
        (_COMPLETE_INPUT, '운송장입력완료'),
        (_TAKE_PRODUCT, '상품인수'),
        (_MOVING, '상품이동중'),
        (_ARRIVAL_HUB, '배달지도착'),
        (_ON_DELIVER, '배송출발'),
        (_ARRIVAL, '배송완료')
    ]

    codes = [
        ('04', 'CJ대한통운'), ('05', '한진택배'), ('08', '롯데택배'),
        ('01', '우체국택배'), ('06', '로젠택배'), ('11', '일양로지스'),
        ('12', 'EMS'), ('14', 'UPS'), ('26', 'USPS'),
        ('22', '대신택배'), ('23', '경동택배'), ('32', '합동택배'),
        ('46', 'CU 편의점택배'), ('24', 'CVSnet 편의점택배s'),
        ('16', '한의사랑택배'), ('17', '천일택배'), ('18', '건영택배'),
        ('28', 'GSMNtoN'), ('29', '에어보이익스프레스'), ('30', 'KGL네트웍스'),
        ('33', 'DHLarcel'), ('37', '판토스'), ('38', 'ECMS Express'),
        ('40', '굿투럭'), ('41', 'GSI Express'), ('42', 'CJ대한통운 국제특송'),
        ('43', '애니트랙'), ('44', '호남택배'), ('47', '우리한방택배'),
        ('48', 'ACI Express'), ('49', 'ACE Express'), ('50', 'GPS Logix'),
        ('51', '성원글로벌카고'), ('52', '세방'), ('55', 'EuroParcel'),
        ('56', 'KGB택배'), ('57', 'Cway Express'), ('58', '하이택배'),
        ('59', '지오로직'), ('60', 'YJS글로벌(영국)'), ('63', '은하쉬핑'),
        ('64', 'FLF퍼레버택배'), ('65', 'YJS글로벌(월드)'), ('66', 'Giant Network Group'),
        ('70', 'LOTOS CORPORATION'), ('71', 'IK물류'), ('72', '성훈물류'), ('73', 'CR로지텍'),
        ('74', '용마로지스'), ('75', '원더스퀵'), ('76', '대ress'), ('78', '2FastExpress'),
        ('99', '롯데택배 해외특송')
    ]  # 택배사코드

    deal = models.OneToOneField(Deal, related_name='delivery', on_delete=models.CASCADE,
                                help_text='판매승인 이후 생성되는 운송장 입력 모델입니다.')

    memo = models.CharField(max_length=100, null=True, blank=True, verbose_name='배송메모')

    mountain = models.BooleanField(verbose_name='도서산간지역유무', default=False)

    address = models.CharField(max_length=200)

    state = models.IntegerField(choices=states, default=1)
    code = models.TextField(choices=codes, null=True, blank=True, verbose_name='택배사코드')
    number = models.CharField(max_length=100, null=True, blank=True, verbose_name='운송장번호')

    # 운송장 번호 입력 시간 : 이 시간을 기준으로 5일 이후 자동으로 deal 의 거래 완료 처리
    number_created_time = models.DateTimeField(null=True, blank=True, help_text="운송장 번호 입력 시간")

    # @property
    #     # def address_str(self):
    #     #     """
    #     #     deal.buyer.address의 property 를 사용하여 string 형태로 return 합니다.
    #     #     :return:
    #     #     """
    #     #     buyer = self.deal.buyer
    #     #     if not hasattr(buyer, 'address'):
    #     #         return None
    #     #     return buyer.address.address


class DeliveryMemo(models.Model):
    memo = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(unique=True)

    class Meta:
        verbose_name = '배송메모 관리'
        verbose_name_plural = '배송메모 관리'

    def __str__(self):
        return self.memo
