# -*- encoding: utf-8 -*-
from django.utils import timezone
from chats.message_models import TextChatMessageTmpl, ImageChatMessageTmpl
from chats.profile_models import ChatSource


def fake_bot_text(text, created_at=None):
    """
    Text -> ChatMessage
    """
    if not created_at:
        created_at = timezone.now()
    bot_source = ChatSource(bot_key='delivery_bot')
    return TextChatMessageTmpl(source=bot_source, text=text).with_created_at(created_at).fake()


def fake_chat_msg_from_contact_reply(reply, room_id=None):
    """
    ContactReply -> ChatMessage
    """
    reply_source = ChatSource(user=reply.author)
    if reply.image_key:
        tmpl = ImageChatMessageTmpl(source=reply_source, image_key=reply.image_key).with_created_at(reply.created_at)
    else:
        tmpl = TextChatMessageTmpl(source=reply_source, text=reply.content).with_created_at(reply.created_at)
    return tmpl.with_room_id(room_id).fake()


def fake_chat_msg_from_answer_reply(reply, room_id=None):
    """
    AnswerReply -> ChatMessage
    """
    reply_source = ChatSource(user=reply.author)
    if reply.image_key:
        tmpl = ImageChatMessageTmpl(source=reply_source, image_key=reply.image_key).with_created_at(reply.created_at)
    else:
        tmpl = TextChatMessageTmpl(source=reply_source, text=reply.content).with_created_at(reply.created_at)
    return tmpl.with_room_id(room_id).fake()


