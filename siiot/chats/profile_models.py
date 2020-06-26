# -*- encoding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

# bot profile
_bot_dict = {}  # dict : bot_key -> bot_class


def _register_bot_profile(cls):
    _bot_dict[cls.key] = cls
    return cls


def get_bot_profile(bot_key):
    return _bot_dict.get(bot_key, None)


@_register_bot_profile
class ChatBotProfile(object):
    key = 'chat_bot'
    profile_image_url = ''
    nickname = _('siiot_assistant')


# chats profiles
class ChatSource(object):
    source_type = None
    source_user = None
    source_bot = None

    def __init__(self, user=None, bot_key=None):
        if user is None and bot_key is None:
            raise Exception('user or bot_key must not be null')
        if user:
            self.source_type = 1
            self.source_user = user
        else:
            self.source_type = 2
            self.source_bot = get_bot_profile(bot_key)
