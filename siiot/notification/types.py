from accounts.models import User

action_types = []
# use_action_types = []

# Notification Action 값으로 NotificationType모델을 접근하기 위한
notification_types = {}

"""
이 Types.py에 모든 Notification의 관한 정보가 입력
이 정보에 대해서 접근해서 실제 Notification을 발송하는 로직은 모두 Notifications.tools에 함수로 정의
단, Business Logic에 의해 그 함수를 부르는 일은 각 필요에 맞는 곳에서 행해짐
"""


def NotificationType(_class):
    action_types.append((_class.action, _class.__name__))
    notification_types[_class.action] = _class
    return _class


# def NotificationButtonUseType(_class):
#     use_action_types.append(_class.action)
#     return _class


class BaseNotificationType(object):
    """
    기본 푸쉬 메시지 세팅
    """

    def __init__(self, list_user):
        self.list_user = list_user

    class Meta:
        abstract = True

    action = None
    is_readable = False  # 리스트에 저장하는가
    is_notifiable = False  # 모든 push는 보내지만, user에게 pop시키지 않는 것들이 있음 push message를 유저에게 표시하는가(list와 별개로 휴대폰 푸쉬)

    def title(self):
        return ""

    def content(self):
        return ""

    def image(self):
        return ""

    def icon(self):
        return ""

    def link(self):
        return ""

    def big_image(self):
        return None

    def target(self):
        return None

    def _from(self):
        return ""

    def get_notification(self):
        from notification.models import Notification
        noti, _ = Notification.objects.get_or_create(
            action=self.action,
            target=self.target(),
            title=self.title(),
            content=self.content(),
            image=self.image(),
            icon=self.icon(),
            big_image=self.big_image(),
            link=self.link(),
            _from=self._from
        )
        return noti

    def send(self):
        from notification.tools import send_push_async
        send_push_async(list_user=self.list_user, notification=self.get_notification())


@NotificationType
class ProductLikeNotice(BaseNotificationType):
    action = 101
    is_readable = True
    is_notifiable = True

    def __init__(self, product, list_user, _from):
        self.product = product
        self._from = _from
        super(ProductLikeNotice, self).__init__(list_user)

    def title(self):
        return "좋아요"

    def content(self):
        _from_nickname = User.objects.get(pk=self._from)
        return "{}: {} 상품에 찜을 눌렀습니다.".format(_from_nickname, self.product.name)

    def image(self):
        return ""

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def link(self):
        return "sii-ot://detail_owner/{}/".format(self.product.id)

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class UnreadMessageNotice(BaseNotificationType):
    action = 102
    is_readable = True
    is_notifiable = True

    def __init__(self, unreadcount, list_user):
        self.unreadcount = unreadcount
        super(UnreadMessageNotice, self).__init__(list_user)

    def title(self):
        return "읽지 않은 메세지"

    def content(self):
        return "{} 개의 읽지 않은 메세지가 있습니다.".format(self.unreadcount)

    def image(self):
        return ""

    def link(self):
        return ""

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]


@NotificationType
class CheckSellConfirmNotice(BaseNotificationType):
    action = 201
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(CheckSellConfirmNotice, self).__init__(list_user)

    def title(self):
        return "판매 승인/거절"

    def content(self):
        return "{} 상품이 결제되었습니다. 판매 승인 또는 거절을 눌러주세요!".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_sale_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class SellerConfirmNotice(BaseNotificationType):
    action = 202
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(SellerConfirmNotice, self).__init__(list_user)

    def title(self):
        return "판매 승인"

    def content(self):
        return "결제한 {} 상품이 판매 승인 되었습니다!".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_purchased_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class SellerRejectNotice(BaseNotificationType):
    action = 203
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(SellerRejectNotice, self).__init__(list_user)

    def title(self):
        return "판매 거절"

    def content(self):
        return "결제한 {} 상품이 판매 거절 되었습니다.".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_purchased_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class DeliverNumNotice(BaseNotificationType):
    action = 204
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(DeliverNumNotice, self).__init__(list_user)

    def title(self):
        return "배송 완료"

    def content(self):
        return "결제한 {} 상품의 운송장 번호가 입력되었습니다!".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_purchased_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class CheckBuyerConfirmNotice(BaseNotificationType):
    action = 205
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(CheckBuyerConfirmNotice, self).__init__(list_user)

    def title(self):
        return "구매 확정"

    def content(self):
        return "{} 상품이 도착하였다면 구매확정버튼을 눌러주시고, 아니라면 시옷 고객센터에 문의해주세요!".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_purchased_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class BuyerConfirmNotice(BaseNotificationType):
    action = 206
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(BuyerConfirmNotice, self).__init__(list_user)

    def title(self):
        return "구매 확정"

    def content(self):
        return "판매한 {} 상품이 구매자에게 잘 도착했습니다!".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_sale_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class SellerCancelNotice(BaseNotificationType):
    action = 207
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(SellerCancelNotice, self).__init__(list_user)

    def title(self):
        return "거래 취소"

    def content(self):
        return "판매자가 {} 상품 거래를 취소했습니다.".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_purchased_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from


@NotificationType
class BuyerCancelNotice(BaseNotificationType):
    action = 208
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user, _from):
        self.transaction = transaction
        self._from = _from
        super(BuyerCancelNotice, self).__init__(list_user)

    def title(self):
        return "거래 취소"

    def content(self):
        return "구매자가 {} 상품 거래를 취소했습니다.".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return "sii-ot://deal_sale_detail/{}/".format(self.transaction.id)

    def icon(self):
        return "https://siiot-media-storage.s3.ap-northeast-2.amazonaws.com/%EC%95%8C%EB%A6%BC_2.png"

    def target(self):
        return self.list_user[0]

    def _from(self):
        return self._from
