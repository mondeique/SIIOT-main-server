from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Notification의 choices 옵션으로 사용하기 위한 리스트
from rest_framework.reverse import reverse

action_types = []
use_action_types = []

# Notification Action 값으로 NotificationType모델을 접근하기 위한
notification_types = {}

"""
이 Types.py에 모든 Notification의 관한 정보가 입력되야함.
이 정보에 대해서 접근해서 실제 Notification을 발송하는 로직은 모두 Notifications.tools에 함수로 정의함.
단, Business Logic에 의해 그 함수를 부르는 일은 각 필요에 맞는 곳에서 행해짐

on_XXX함수 추가시 맨 아래 추가하고 test_models.py 에도 추가바람

confluence 푸시 기획과 동기화 필수
"""


def NotificationType(_class):
    action_types.append((_class.action, _class.__name__))
    notification_types[_class.action] = _class
    return _class


def NotificationButtonUseType(_class):
    use_action_types.append(_class.action)
    return _class


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
        return "siiot://home/"

    def extras(self):
        return {}

    def big_image(self):
        return None

    def target(self):
        return None

    def get_notification(self):
        from notification.models import Notification
        noti = Notification.objects.create(
            action=self.action,
            target=self.target(),
            title=self.title(),
            content=self.content(),
            image=self.image(),
            icon=self.icon(),
            big_image=self.big_image(),
            link=self.link()
        )
        return noti

    def send(self):
        from notification.tools import send_push_async
        send_push_async(list_user=self.list_user, notification=self.get_notification(),
                        extras=self.extras())


@NotificationType
class ProductLikeNotice(BaseNotificationType):
    action = 101
    is_readable = True
    is_notifiable = True

    def __init__(self, product, list_user):
        self.product = product
        super(ProductLikeNotice, self).__init__(list_user)

    def title(self):
        return "product_like"

    def content(self):
        return "{} 상품에 찜을 눌렀습니다.".format(self.product.name)

    # TODO : siiot icon
    def image(self):
        return ""

    # TODO : Client Deep Link Format
    def link(self):
        return "siiot://product/{}/detail/".format(self.product.id)

    def target(self):
        return self.list_user[0].id


@NotificationType
class UnreadMessageNotice(BaseNotificationType):
    action = 102
    is_readable = True
    is_notifiable = True

    def __init__(self, unreadcount, list_user):
        self.unreadcount = unreadcount
        super(UnreadMessageNotice, self).__init__(list_user)

    def title(self):
        return "unread_message"

    def content(self):
        return "{} 개의 읽지 않은 메세지가 있습니다.".format(self.unreadcount)

    def image(self):
        return ""

    def link(self):
        return ""

    def target(self):
        return self.list_user[0].id


@NotificationType
class CheckSellConfirmNotice(BaseNotificationType):
    action = 201
    is_readable = True
    is_notifiable = True

    def __init__(self, transaction, list_user):
        self.transaction = transaction
        super(CheckSellConfirmNotice, self).__init__(list_user)

    def title(self):
        return "check_sellconfirm"

    def content(self):
        return "{} 상품이 결제되었습니다. 판매 승인 또는 거절을 눌러주세요!".format(self.transaction.deal.trades.first().product.name)

    def image(self):
        return ""

    def link(self):
        return ""

    def target(self):
        return self.list_user[0].id


@NotificationType
class SellerConfirmNotice(BaseNotificationType):
    action = 202
    is_readable = True
    is_notifiable = True

    def __init__(self, event_notice, list_user):
        self.event_notice = event_notice
        super(SellerConfirmNotice, self).__init__(list_user)

    def title(self):
        return "notification_new_event"

    def content(self):
        return self.event_notice.title

    def image(self):
        return u"https://qanda-server-storage.s3.amazonaws.com/eventxhdpi.png"

    def link(self):
        return u"qanda://event/student/{}/".format(self.event_notice.id)

    def target(self):
        return self.event_notice.id


@NotificationType
class SellerRejectNotice(BaseNotificationType):
    action = 203
    is_readable = True
    is_notifiable = True

    def __init__(self, event_notice, list_user):
        self.event_notice = event_notice
        super(SellerRejectNotice, self).__init__(list_user)

    def title(self):
        return "notification_new_event"

    def content(self):
        return self.event_notice.title

    def image(self):
        return u"https://qanda-server-storage.s3.amazonaws.com/eventxhdpi.png"

    def link(self):
        return u"qanda://event/student/{}/".format(self.event_notice.id)

    def target(self):
        return self.event_notice.id


@NotificationType
class DeliverNumNotice(BaseNotificationType):
    action = 204
    is_readable = True
    is_notifiable = True

    def __init__(self, event_notice, list_user):
        self.event_notice = event_notice
        super(DeliverNumNotice, self).__init__(list_user)

    def title(self):
        return "notification_new_event"

    def content(self):
        return self.event_notice.title

    def image(self):
        return u"https://qanda-server-storage.s3.amazonaws.com/eventxhdpi.png"

    def link(self):
        return u"qanda://event/student/{}/".format(self.event_notice.id)

    def target(self):
        return self.event_notice.id


@NotificationType
class CheckBuyerConfirmNotice(BaseNotificationType):
    action = 205
    is_readable = True
    is_notifiable = True

    def __init__(self, event_notice, list_user):
        self.event_notice = event_notice
        super(CheckBuyerConfirmNotice, self).__init__(list_user)

    def title(self):
        return "notification_new_event"

    def content(self):
        return self.event_notice.title

    def image(self):
        return u"https://qanda-server-storage.s3.amazonaws.com/eventxhdpi.png"

    def link(self):
        return u"qanda://event/student/{}/".format(self.event_notice.id)

    def target(self):
        return self.event_notice.id


@NotificationType
class BuyerConfirmNotice(BaseNotificationType):
    action = 206
    is_readable = True
    is_notifiable = True

    def __init__(self, event_notice, list_user):
        self.event_notice = event_notice
        super(BuyerConfirmNotice, self).__init__(list_user)

    def title(self):
        return "notification_new_event"

    def content(self):
        return self.event_notice.title

    def image(self):
        return u"https://qanda-server-storage.s3.amazonaws.com/eventxhdpi.png"

    def link(self):
        return u"qanda://event/student/{}/".format(self.event_notice.id)

    def target(self):
        return self.event_notice.id
