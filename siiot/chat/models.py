from django.db import models
from django.conf import settings
from core.fields import S3ImageKeyField

from payment.models import Deal
from products.models import Product


def img_directory_path_message(instance, filename):
    return 'chatroom/{}/message/{}'.format(instance.room.id, filename)


class ChatRoom(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='seller_chat_rooms',
                               on_delete=models.SET_NULL)
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='buyer_chat_rooms',
                              on_delete=models.SET_NULL)
    seller_active = models.BooleanField(default=True, null=True, help_text='판매자 웹소켓 채팅이 가능할 경우 True')
    buyer_active = models.BooleanField(default=True, null=True, help_text='구매자 웹소켓 채팅이 가능할 경우 True')
    deal = models.OneToOneField(Deal, help_text='채팅방에 연관된 deal id', null=True,
                                related_name='chat_room', on_delete=models.SET_NULL)
    product = models.OneToOneField(Product, help_text='채팅방에 연관된 product_id', null=True,
                                   related_name='chat_room', on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    # is_active = models.BooleanField(default=True, null=True)


class ChatMessage(models.Model):
    MESSAGE_TYPES = (
        # 추후 업데이트는 SIIOT BOT이 CARD 형태로 전달하기 떄문에 message_type을 늘리거나 action_code 작성 필요
        (1, 'text'),
        (2, 'image')
    )
    message_type = models.IntegerField(choices=MESSAGE_TYPES, db_index=True, default=1)
    room = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    text = models.TextField()
    # message_image = models.ImageField(null=True, blank=True, upload_to=img_directory_path_message)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, help_text='상대방 입장에서 web socket 접속할 때 바뀌는 field')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, related_name='owner_message',
                              on_delete=models.SET_NULL)
    seller_visible = models.BooleanField(default=True, help_text='셀러에게 보여지지 않는 경우 false')
    buyer_visible = models.BooleanField(default=True, help_text='바이어에게 보여지지 않는 경우 false')

    class Meta:
        ordering = ['created_at']


class ChatMessageImages(models.Model):
    message = models.ForeignKey(ChatMessage, related_name="images", on_delete=models.CASCADE)
    image_key = S3ImageKeyField()

    @property
    def image_url(self):
        return self.image_key.url