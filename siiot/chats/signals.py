# -*- encoding: utf-8 -*-
import requests

from django.db.models import signals
from django.dispatch import receiver

# from chats.models import ChatMessage

#
# @receiver(signals.post_save, sender=ChatMessage)
# def deliver_chat_message_to_websocket(sender, instance, created, **kwargs):
#     """
#     ChatMessage를 채팅서버의 room 및 user 등에게 deliver합니다.
#     v2 client 및 web client 등, websocket에 접속하지 않는 사용자에 의해 생성된 chat_msg를 처리할 수 있습니다.
#     - reference: (채팅서버) chats.views.ChatMessageViewSet.deliver API
#     """
#     chat_msg = instance
#     endpoint = 'http://{domain}/api/v1/chats/message/{id}/deliver/'.format(domain=chat_msg.room.domain,
#                                                                           id=chat_msg.id)
#     resp = requests.post(endpoint)
#     # TODO: logging??
#
# #
# @receiver(signals.post_save, sender=ChatRoom)
# def connect_contact(sender, instance, created, **kwargs):
#     """
#     room_type="contact"인 ChatRoom이 만들어질 경우, 사용자의 contact에 chat_room을 연동하고 채팅내역을 복사합니다.
#      * 기존에 chat_room 이 존재하여도 작동합니다. 기존 chat_room의 연결은 끊깁니다.
#     :return:
#     """
