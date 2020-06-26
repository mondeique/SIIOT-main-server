# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from collections import Mapping
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from raven.contrib.django.models import client as raven_client
from chats.command import *
from chats.profile_models import ChatSource
from core.fields import S3ImageKeyField
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class TestChatMessage(models.Model):

    # source(=author) fields
    SOURCE_TYPES = (
        (1, 'user'),
        (2, 'bot'),
    )
    source_type = models.IntegerField(choices=SOURCE_TYPES, db_index=True)
    source_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_messages', blank=True, null=True,
                                    on_delete=models.CASCADE)
    source_bot_key = models.CharField(max_length=30, blank=True, db_index=True)

    MESSAGE_TYPES = (
        # DON'T CHANGE THOSE STRINGS!! (used with "get_message_type_display")
        (1, 'text'),
        (2, 'image'),
        (3, 'template'),
        (4, 'audio'),
        (5, 'video'),
        (6, 'postback'),
        (7, 'instant_command'),
        (8, 'lottie_emoji'),

        (10, 'sales_approval'),  # 판매 승인 시
        (11, 'delivery'),  # 판매자 운송장 번호 입력 시
        (12, 'confirm_purchase'),  # 구매 확정 시

        (20, 'purchase_cancle'),  # 구매 취소 시
        (21, 'purchase_cancle_request'),  # 구매 취소 요청 시
        (22, 'purchase_cancle_reject'),  # 구매 취소 거절 시
    )

    message_type = models.IntegerField(choices=MESSAGE_TYPES, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
    is_read = models.BooleanField(default=False)

    room = models.ForeignKey('TestChatRoom', related_name='messages', on_delete=models.CASCADE)
    code = models.CharField(max_length=100, db_index=True)
    image_key = S3ImageKeyField(blank=True, null=True)  # 이미지 보낼 때
    # content_url = models.CharField(max_length=300, blank=True)
    # lottie_emoji_key = models.CharField(max_length=30, blank=True)
    # caption = models.CharField(max_length=30, blank=True)
    uri = models.CharField(max_length=300, blank=True, null=True)
    version = models.IntegerField(default=1)  # client 에서 보내야함

    # target fields
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='targeted_chat_messages',
                                    blank=True, null=True, on_delete=models.CASCADE)
    is_hidden = models.BooleanField(default=True)

    def __str__(self):
        return str(self.id)

    def characters(self):
        """
        Toy function to count body characters.
        :return: body's char number
        """
        return len(self.text)

    def notify_ws_clients(self):
        """
        Inform client there is a new message.
        """
        notification = {
            'type': 'recieve_group_message',
            'message': '{}'.format(self.id)
        }

        channel_layer = get_channel_layer()
        print(channel_layer)
        print("buyer.id {}".format(self.room.buyer_id))
        print(channel_layer.group_send)
        async_to_sync(channel_layer.group_send)("chat_{}".format(self.room_id), notification)
        # async_to_sync(channel_layer.group_send)("chat_{}".format(self.room.seller_id), notification)

    def save(self, *args, **kwargs):
        """
        Trims white spaces, saves the message and notifies the recipient via WS
        if the message is new.
        """
        new = self.id
        self.text = self.text.strip()  # Trimming whitespaces from the body
        super(TestChatMessage, self).save(*args, **kwargs)
        if new is None:
            self.notify_ws_clients()


class TestChatRoom(models.Model):
    deal_id = models.PositiveIntegerField(null=True, blank=True,
                                          help_text="deal model id 입니다. Contact에도 활용할 수 있게 nullable 하게 하였습니다.")

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="buyer_chat_rooms",
                              help_text='채팅은 구매자가 생성합니다.')

    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_chat_rooms')

    # 접속 시간 필드 : ChatMessage 의 is_read 를 관리합니다.
    buyer_connected_time = models.DateTimeField(null=True, blank=True, help_text='접속시 update 합니다.')
    buyer_disconnected_time = models.DateTimeField(null=True, blank=True, help_text='접속해제시 update 합니다.')
    seller_connected_time = models.DateTimeField(null=True, blank=True)
    seller_disconnected_time = models.DateTimeField(null=True, blank=True)

    room_type = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    test = models.TextField()

    class Meta:
        managed = True




# class ChatRoom(models.Model):
#     room_type = models.CharField(max_length=30, db_index=True)
#     owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_rooms', on_delete=models.CASCADE)
#     active = models.BooleanField(default=True, help_text='웹소켓 채팅이 가능할 경우 True')
#     version = models.IntegerField(blank=True, null=True, help_text='채팅 기능의 버전')
#     created_at = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         verbose_name_plural = '채팅룸'
#
#     def __str__(self):
#         return '[{}] (owner_id={}) (room_type={}) (active={})'.format(self.id, self.owner_id, self.room_type, self.active)
#
#     def read_tag(self, user, key, default=None):
#         """
#         (room, user, key)의 태그 값을 읽습니다. 값이 여러 개 존재하면, 마지막 값을 반환합니다.
#         :return: integer or string value
#         """
#         tag_value = self.tag_values.filter(user=user, key=key).order_by('id').last()
#         if not tag_value:
#             return default
#         return tag_value.value
#
#     def write_int_tag(self, user, key, value):
#         """
#         (room, user, key)의 int 태그 값을 만듭니다. 이미 태그가 존재하면, 값을 업데이트합니다.
#         """
#         assert isinstance(value, six.integer_types), 'write_int_tag assertion failed'
#         defaults = {'value_type': 1, 'string_value': '', 'int_value': value, 'json_value': None}
#         self.tag_values.update_or_create(user=user, key=key, defaults=defaults)
#
#     def write_string_tag(self, user, key, value):
#         """
#         (room, user, key)의 string 태그 값을 만듭니다. 이미 태그가 존재하면, 값을 업데이트합니다.
#         """
#         assert isinstance(value, six.string_types), 'write_string_tag assertion failed'
#         defaults = {'value_type': 2, 'string_value': value, 'int_value': None, 'json_value': None}
#         self.tag_values.update_or_create(user=user, key=key, defaults=defaults)
#
#     def write_json_tag(self, user, key, value):
#         """
#         (room, user, key)의 json 태그 값을 만듭니다. 이미 태그가 존재하면, 값을 업데이트합니다.
#         """
#         assert isinstance(value, Mapping), 'write_json_tag assertion failed'
#         defaults = {'value_type': 3, 'string_value': '', 'int_value': None, 'json_value': value}
#         self.tag_values.update_or_create(user=user, key=key, defaults=defaults)
#
#     def delete_tag(self, user, key):
#         """
#         (room, user, key)의 태그 값을 삭제합니다.
#         :return: integer or string value
#         """
#         self.tag_values.filter(user=user, key=key).delete()
#
#     def update_ic_state(self, user, key, value):
#         ic_key = 'ic_state$' + key
#         # Documentation : see 채팅서버
#         if isinstance(value, six.integer_types):
#             self.write_int_tag(user=user, key=ic_key, value=value)
#         elif isinstance(value, six.string_types):
#             self.write_string_tag(user=user, key=ic_key, value=value)
#         elif isinstance(value, Mapping):
#             self.write_json_tag(user=user, key=ic_key, value=value)
#
#     def read_all_ic_states(self, user):
#         # Documentation : see 채팅서버
#         result = {}
#         for tag_value in self.tag_values.filter(key__startswith='ic_state$'):
#             key = tag_value.key[9:]
#             result[key] = tag_value.value
#         return result
#
#     @property
#     def domain(self):
#         domain = 'chat_server_domain'
#         return domain
#
#     @property
#     def websocket_url(self):
#         # 새로운 채팅에서 사용하는 routing 규칙을 따름
#         return 'ws://{domain}/chats/{room_type}/{pk}/'.format(domain=self.domain, room_type=self.room_type, pk=self.id)
#
#     def get_chat_room_url(self):
#         from rest_framework.reverse import reverse
#         return '<a href="%s" target="_blank">%s</a>' % (reverse('chat_room', kwargs={'room_id': self.id}), self.id)
#
#     def get_chat_room_link(self):
#         return self.get_chat_room_url()
#
#     get_chat_room_link.allow_tags = True
#     get_chat_room_link.short_description = u'웹 채팅룸 url'
#
#     def get_role_dict(self):
#         """
#         ChatUserSerializer에서 사용자의 role 정보를 알기 위해 사용할 수 있는, role_dict를 반환합니다.
#         """
#         role_dict = {}
#         for participant in self.participants.all():
#             role_dict[participant.user_id] = participant.role
#         return role_dict
#
#     class ChatRoomFull(Exception):
#         pass
#
#     def join(self, user, role):
#         """
#         사용자를 방에 참여시킵니다. may raise ChatRoomFull
#         """
#         # join
#         participant_obj, created = ChatRoomParticipant.objects.update_or_create(room=self, user=user,
#                                                                                 defaults={'role': role})
#         if created:
#             self._notify_chatserver_user_joined(participant_obj=participant_obj)
#
#     def leave(self, user):
#         """
#         사용자를 방에서 제외시킵니다.
#         """
#         deleted_count, _ = self.participants.filter(user=user).delete()
#         if deleted_count > 0:
#             self._notify_chatserver_user_left(user=user)
#
#     def _notify_chatserver_user_joined(self, participant_obj):
#         """
#         채팅방에 사용자가 참여한 경우, 참여했다고 채팅서버에 알려줍니다.
#         - reference : chats.views.ChatRoomViewSet.user_joined API
#           이 API에서 channel server level의 기능들(ex. 다른 사용자에게 알리기)이 구현됩니다.
#         TODO: make me async
#         """
#         try:
#             endpoint = 'http://{domain}/api/v1/chats/room/{room_id}/user_joined/'.format(domain=self.domain,
#                                                                                         room_id=self.id)
#             resp = requests.post(endpoint, data={'user_id': participant_obj.user_id})
#             resp.raise_for_status()
#         except:
#             raven_client.captureException()
#
#     def _notify_chatserver_user_left(self, user):
#         """
#         채팅방에서 사용자가 나가는 경우, 나갔다고 채팅서버에 알려줍니다.
#         - reference : chats.views.ChatRoomViewSet.user_left API
#         TODO: make me async
#         """
#         try:
#             endpoint = 'http://{domain}/api/v1/chats/room/{room_id}/user_left/'.format(domain=self.domain,
#                                                                                       room_id=self.id)
#             resp = requests.post(endpoint, data={'user_id': user.id})
#             resp.raise_for_status()
#         except:
#             raven_client.captureException()
#
#
# class ChatRoomTagValue(models.Model):
#     """
#     Chatting handler에서 필요한 값을 임시로 저장할 때 사용합니다.
#     """
#     room = models.ForeignKey(ChatRoom, related_name='tag_values', on_delete=models.CASCADE)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_tag_values', on_delete=models.CASCADE)
#     key = models.CharField(max_length=200, db_index=True)
#     VALUE_TYPES = (
#         (1, 'int'),
#         (2, 'string'),
#         (3, 'json'),
#     )
#     value_type = models.IntegerField(choices=VALUE_TYPES, db_index=True)
#     int_value = models.IntegerField(blank=True, null=True, db_index=True)
#     string_value = models.CharField(max_length=200, blank=True, db_index=True)
#     json_value = jsonfield.JSONField(default=dict, null=True)  # TODO: remove null=True after migration
#
#     @property
#     def value(self):
#         if self.value_type == 1:
#             return self.int_value
#         elif self.value_type == 2:
#             return self.string_value
#         elif self.value_type == 3:
#             return self.json_value
#         return None
#
#     class Meta:
#         index_together = (
#             ('room', 'user', 'key'),
#         )
#
#     def get_value_staff(self):
#         return dict(self.VALUE_TYPES).get(self.value_type)
#
#     get_value_staff.short_description = 'value'
#
#
# class SourceType(object):
#     USER = 1
#     BOT = 2
#
#
# class ChatMessage(models.Model):
#     # normal fields
#     MESSAGE_TYPES = (
#         # DON'T CHANGE THOSE STRINGS!! (used with "get_message_type_display")
#         (1, 'text'),
#         (2, 'image'),
#         (3, 'template'),
#         (4, 'audio'),
#         (5, 'video'),
#         (6, 'postback'),
#         (7, 'instant_command'),
#     )
#     message_type = models.IntegerField(choices=MESSAGE_TYPES, db_index=True)
#     room = models.ForeignKey(ChatRoom, related_name='messages', null=True, on_delete=models.SET_NULL)
#     text = models.TextField()
#     code = models.CharField(max_length=100, db_index=True)
#     image_key = S3ImageKeyField(blank=True, null=True)
#     content_url = models.CharField(max_length=300, blank=True)
#     lottie_emoji_key = models.CharField(max_length=30, blank=True)
#     caption = models.CharField(max_length=30, blank=True)
#     uri = models.CharField(max_length=300, blank=True)
#     version = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add=True, db_index=True)
#
#     # source(=author) fields
#     SOURCE_TYPES = (
#         (1, 'user'),
#         (2, 'bot'),
#     )
#     source_type = models.IntegerField(choices=SOURCE_TYPES, db_index=True)
#     source_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_messages', blank=True, null=True, on_delete=models.CASCADE)
#     source_bot_key = models.CharField(max_length=30, blank=True, db_index=True)
#
#     # template data fields
#     template = jsonfield.JSONField(default=dict)
#
#     # target fields
#     target_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='targeted_chat_messages',
#                                     blank=True, null=True, on_delete=models.SET_NULL)
#     is_hidden = models.BooleanField(default=True)
#
#     # action & postback fields
#     token = models.UUIDField(unique=True, db_index=True, default=uuid.uuid4)
#     postback_parent = models.ForeignKey('self', related_name='postback_children', blank=True, null=True, on_delete=models.CASCADE)
#     postback_value = models.CharField(max_length=100, blank=True, db_index=True)  # DEPRECATED?
#     extras = jsonfield.JSONField(default=dict)
#
#     # generic foreign key field
#     object_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)
#
#     # invalidated
#     invalidated = models.BooleanField(default=False)
#
#     # client_handler_version : 메세지를 생성한 client의 버전 (bot 및 user 메세지 모두 포함)
#     client_handler_version = models.IntegerField(blank=True, null=True, db_index=True)
#     # target_handler_version : 특정 버전 handler를 사용하는 client에게만 메세지를 보낼 경우 사용
#     target_handler_version = models.IntegerField(blank=True, null=True, db_index=True)
#
#     @property
#     def handler_name(self):
#         return self.code.split('$')[0]
#
#     @property
#     def action_code(self):
#         return self.code.split('$')[1]
#
#     @property
#     def source(self):
#         if self.source_type == SourceType.USER:
#             return ChatSource(user=self.source_user)
#         else:
#             return ChatSource(bot_key=self.source_bot_key)
#
#     @property
#     def original_content_url(self):
#         if self.image_key:
#             return self.image_key.url
#         elif self.content_url:
#             return self.content_url
#         return None
#
#     @property
#     def preview_image_url(self):
#         return self.original_content_url
#
#     @property
#     def command(self):
#         if self.message_type == 7 and \
#                 'command_code' in self.extras and \
#                 'postback_message_code' in self.extras and \
#                 'params' in self.extras:
#             description = get_command_class(self.extras['command_code']).description \
#                 if get_command_class(self.extras['command_code']) else ''
#
#             return {
#                 'code': self.extras['command_code'],
#                 'postback_message_code': self.extras['postback_message_code'],
#                 'params': self.extras['params'],
#                 'description': description,
#             }
#         return None
#
#     def to_simple_text(self):
#         if self.message_type == 2:
#             return _('(photo)')
#         return self.text
#
#
# class ChatRoomParticipant(models.Model):
#     """
#     채팅방 참여자 정보를 관리하기 위한 모델
#     """
#     room = models.ForeignKey(ChatRoom, related_name='participants', on_delete=models.CASCADE)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_participants', on_delete=models.CASCADE)
#     role = models.CharField(max_length=100, blank=True, db_index=True)
#
#     class Meta:
#         unique_together = (
#             ('room', 'user'),
#         )
#         index_together = (
#             ('room', 'user'),
#         )
#
#
# class ChatRoomReportHistory(models.Model):
#     """
#     채팅방에서 사용자를 신고한 기록을 저장하기 위한 모델입니다.
#     """
#     room = models.ForeignKey(ChatRoom, related_name='report_histories', null=True, on_delete=models.SET_NULL)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_reported_histories', null=True,
#                              help_text='신고 대상 사용자', on_delete=models.SET_NULL)
#     reporter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_reporter_histories', null=True,
#                                  help_text='신고자', on_delete=models.SET_NULL)
#     reason = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#
#
# class ChatRoomResult(models.Model):
#     room = models.ForeignKey(ChatRoom, related_name='results', null=True, on_delete=models.SET_NULL)
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='chat_room_results', help_text='기록을 남기는 유저', on_delete=models.CASCADE)
#     result = models.CharField(max_length=100)
#     elapsed = models.IntegerField(help_text='채팅을 보면서 경과한 시간 (milliseconds)')
#     created_at = models.DateTimeField(auto_now_add=True)
