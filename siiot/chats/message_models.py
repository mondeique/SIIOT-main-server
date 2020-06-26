# # -*- encoding: utf-8 -*-
# from collections import Mapping
# from uuid import UUID
#
# # from chats.models import SourceType, ChatMessage
# from chats.profile_models import ChatSource
# # from chats.serializers import ChatMessageWriteSerializer, ChatTeacherSerializer
#
#
# #
# # Base classes
# #
# class Serializable(Mapping):
#     """
#     클래스를 통째로 Serializer에 data 인자로 전달할 수 있도록, dict-like interface를 구현합니다.
#     - ex :
#         tmpl = MessageTmpl(...)
#         serializer = ChatMessageWriteSerializer(data=tmpl)  # tmpl is valid (dict-like object)
#     이 클래스를 상속받는 경우, Meta.fields 를 구현하여야 합니다.
#     """
#
#     class Meta:
#         fields = ()
#
#     # impl for Mapping
#     def __getitem__(self, key):
#         if not hasattr(self, key):
#             raise KeyError(key)
#         initial_attr = getattr(self, key)
#         if isinstance(initial_attr, Serializable):
#             attr = dict(initial_attr)
#         elif isinstance(initial_attr, list):
#             attr = list(map(lambda x: dict(x) if isinstance(x, Serializable) else x))
#         else:
#             attr = initial_attr
#         return attr
#
#     def __iter__(self):
#         for field in self._get_valid_fields():
#             yield field
#
#     def __len__(self):
#         return len(self._get_valid_fields())
#
#     # show only valid fields
#     def _get_valid_fields(self):
#         return [field for field in self.Meta.fields if hasattr(self, field)]
#
#
# class MessageTmplBase(Serializable):
#     """
#     Base class for Message template.
#     MessageTmpl 객체는 ChatMessageSerializer에 전달하여 object로 저장하거나,
#     또는 on-the-fly 로 JSON-serialized message를 생성할 수 있습니다.
#     """
#
#     class Meta:
#         fields = ChatMessageWriteSerializer.Meta.fields
#
#     def __init__(self, source,
#                  action_code='chats'):
#         """
#         :param action_code: 현재 만들고 있는 메세지(=self) 의 action_code
#         """
#         self.source = source
#         self._handler_name = None
#         self.action_code = action_code
#         self.created_at = None
#
#     #
#     # getters
#     #
#     @property
#     def handler_name(self):
#         if not self._handler_name:
#             return 'chats'
#         return self._handler_name
#
#     @handler_name.setter
#     def handler_name(self, handler_name):
#         self._handler_name = handler_name
#
#     @property
#     def source_type(self):
#         return self.source.source_type
#
#     @property
#     def source_user(self):
#         if self.source.source_user:
#             return self.source.source_user.id
#         return None
#
#     @property
#     def source_bot_key(self):
#         if self.source.source_bot:
#             return self.source.source_bot.key
#         return ''
#
#     @property
#     def code(self):
#         return self.handler_name + '$' + self.action_code
#
#     #
#     # builder pattern setters
#     # - TODO: 헷갈리는 부분이므로 문서화 해야 함.
#     #
#     def with_handler_name(self, handler_name):
#         self.handler_name = handler_name
#         return self
#
#     def with_created_at(self, created_at):
#         """
#         ChatMessage 객체 없이, Tmpl->JSON 으로 serialize할 때 사용.
#         """
#         self.created_at = created_at
#         return self
#
#     def with_room_id(self, room_id):
#         """
#         write-only. (FIXME: docstring & arg name is ugly)
#         """
#         self.room = room_id
#         return self
#
#     def with_target_user_id(self, target_user_id):
#         """
#         write-only. (FIXME: docstring & arg name is ugly)
#         """
#         self.target_user = target_user_id
#         return self
#
#     def with_postback_parent_id(self, postback_parent_id):
#         """
#         write-only. (FIXME: docstring & arg name is ugly)
#         """
#         self.postback_parent = postback_parent_id
#         return self
#
#     def with_action_code(self, action_code):
#         """
#         write-only. (FIXME: docstring & arg name is ugly)
#         """
#         if action_code:
#             self.action_code = action_code
#         else:
#             self.action_code = 'chats'
#         return self
#
#     def with_client_handler_version(self, client_handler_version):
#         """
#         write-only. (FIXME: docstring & arg name is ugly)
#         """
#         self.client_handler_version = client_handler_version
#         return self
#
#     def with_target_handler_version(self, target_handler_version):
#         """
#         write-only. (FIXME: docstring & arg name is ugly)
#         """
#         self.target_handler_version = target_handler_version
#         return self
#
#     #
#     # python magics
#     #
#     def __str__(self):
#         if self.source_type == SourceType.USER:
#             source_description = u'user={}'.format(self.source_user)
#         else:
#             source_description = u'bot={}'.format(self.source_bot_key)
#         return u'{}(code={}, {})'.format(self.__class__.__name__, self.code, source_description)
#
#     def __unicode__(self):
#         return self.__str__()
#
#     def __repr__(self):
#         return self.__unicode__()
#
#     #
#     # impl
#     #
#     def save(self):
#         """
#         ChatMessage에 저장합니다.
#         :return: ChatMessage object
#         :raises: serializers.ValidationError
#         """
#         serializer = ChatMessageWriteSerializer(data=self)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.create(serializer.validated_data)
#         return instance
#
#     def update(self, chat_msg):
#         """
#         ChatMessage 객체에 tmpl을 적용합니다.
#         :param chat_msg: ChatMessage object
#         :return: ChatMessage object
#         :raises: serializers.ValidationError
#         """
#         serializer = ChatMessageWriteSerializer(chat_msg, data=self)
#         serializer.is_valid(raise_exception=True)
#         instance = serializer.update(chat_msg, serializer.validated_data)
#         return instance
#
#     def fake(self):
#         """
#         save하지 않은 ChatMessage 객체를 만듭니다.
#         :return: ChatMessage object (doesn't have pk value)
#         """
#         serializer = ChatMessageWriteSerializer(data=self)
#         serializer.is_valid(raise_exception=True)
#         instance = ChatMessage(**serializer.validated_data)
#         if self.created_at:
#             instance.created_at = self.created_at  # serializer doesn't write created_at, so set it manually
#         return instance
#
#
# class TextMessageMixin(object):
#     @property
#     def message_type(self):
#         return 1
#
#
# class ImageMessageMixin(object):
#     image_key = None
#
#     @property
#     def message_type(self):
#         return 2
#
#
# #
# # Basic Messages Implementations
# #
# class TextChatMessageTmpl(MessageTmplBase, TextMessageMixin):
#     def __init__(self, source, text, action_code=None):
#         super(TextChatMessageTmpl, self).__init__(source)
#         self.text = text
#         if action_code:
#             self.action_code = action_code
#
#
# class ImageChatMessageTmpl(MessageTmplBase, ImageMessageMixin):
#     def __init__(self, source,
#                  image_key=None,
#                  content_url=None,
#                  caption=''):
#         super(ImageChatMessageTmpl, self).__init__(source)
#         assert image_key or content_url, 'ImageChatMessageTmpl error. image_key and content_url are both None'
#         if image_key:
#             if isinstance(image_key, UUID):
#                 image_key = str(image_key)
#             self.image_key = image_key
#         if content_url:
#             self.content_url = content_url
#         self.caption = caption
#
#
# class LottieEmojiChatMessageTmpl(MessageTmplBase):
#     @property
#     def message_type(self):
#         return 8
#
#     def __init__(self, source, lottie_emoji_key, action_code=None):
#         super(LottieEmojiChatMessageTmpl, self).__init__(source)
#         self.lottie_emoji_key = lottie_emoji_key
#         if action_code:
#             self.action_code = action_code
#
#
# class UserPostbackChatMessageTmpl(MessageTmplBase):
#     """
#     사용자가 전송한 Postback message를 다룹니다.
#      * REVIEW ME : 특수한 케이스를 특수하게 handling하는 건데, Tmpl 정의에 맞게 올바르게 구현한걸까?
#      * (refac in progress... sad...)
#     """
#
#     @property
#     def message_type(self):
#         # naive implementation. FIXME
#         if self.text:
#             return 1
#         elif self.image_key:
#             return 2
#         return 6  # hidden
#
#     def __init__(self, source, code, text, image_key, extras):
#         super(UserPostbackChatMessageTmpl, self).__init__(source)
#         self.text = text
#         self.image_key = image_key
#         self.extras = extras
#         self.is_hidden = (self.message_type == 6)
#         # FIXME: Below codes may raise exception. Should I handle it?
#         handler_name, action_code = code.split('$')
#         self.handler_name = handler_name
#         self.action_code = action_code
#
#
# #
# # Action models
# #
# class UriAction(object):
#     def __init__(self, label, uri, is_hidden=False):
#         self.label = label
#         self.uri = uri
#         self.is_hidden = is_hidden
#
#     def to_serializable(self):
#         return {
#             'type': 'uri',
#             'label': self.label,
#             'uri': self.uri,
#             'is_hidden': self.is_hidden,
#         }
#
#
# class PostbackAction(object):
#     def __init__(self, message_code, label, params=None, is_hidden=False):
#         if params is None:
#             params = {}
#         self.message_code = message_code
#         self.label = label
#         self.params = params
#         self.is_hidden = is_hidden
#
#     def to_serializable(self):
#         # param에 항상 label을 같이 전송한다.
#         new_params = self.params.copy()
#         new_params['label'] = self.label
#         return {
#             'type': 'postback',
#             'message_code': self.message_code,
#             'label': self.label,
#             'params': new_params,
#             'is_hidden': self.is_hidden,
#         }
#
#
# #
# # Template messages
# #
# class CarouselColumn(object):
#     def __init__(self, thumbnail_image_url, actions):
#         self.thumbnail_image_url = thumbnail_image_url
#         self.actions = actions
#
#     def to_serializable(self):
#         return {
#             'thumbnail_image_url': self.thumbnail_image_url,
#             'actions': [action.to_serializable() for action in self.actions],
#         }
#
#
# class CarouselMessageTmplBase(MessageTmplBase):
#     @property
#     def message_type(self):
#         return 3
#
#     def get_columns(self):
#         raise NotImplemented
#
#     @property
#     def template(self):
#         return {
#             'type': 'carousel',
#             'columns': [col.to_serializable() for col in self.get_columns()]
#         }
#
#
# class ButtonsMessageTmpl(MessageTmplBase):
#     def __init__(self, source, action_code, actions, text='', thumbnail_image_url=None):
#         super(ButtonsMessageTmpl, self).__init__(source=source, action_code=action_code)
#         self.text = text
#         self.actions = actions
#         self.thumbnail_image_url = thumbnail_image_url
#
#     @property
#     def message_type(self):
#         return 3
#
#     @property
#     def template(self):
#         return {
#             'type': 'buttons',
#             'text': self.text,
#             'thumbnail_image_url': self.thumbnail_image_url,
#             'actions': [action.to_serializable() for action in self.actions]
#         }
#
#
# class HeaderMessageTmpl(MessageTmplBase):
#     def __init__(self, source, action_code, text=''):
#         super(HeaderMessageTmpl, self).__init__(source=source, action_code=action_code)
#         self.text = text
#
#     @property
#     def message_type(self):
#         return 3
#
#     @property
#     def template(self):
#         return {
#             'type': 'header',
#             'text': self.text,
#         }
#
#
# #
# # Instant command messages
# #
# class InstantCommandMessageTmpl(MessageTmplBase):
#     """
#     봇이 client에게 is_hidden=True로 보내는 Predefined command 메세지를 다룹니다.
#     """
#     @property
#     def message_type(self):
#         return 7
#
#     def __init__(self, source, command_code, postback_message_code='', params=None):
#         super(InstantCommandMessageTmpl, self).__init__(source)
#         if params is None:
#             params = {}
#         self.command_code = command_code
#         self.postback_message_code = postback_message_code
#         self.params = params
#
#     @property
#     def extras(self):
#         return {
#             'command_code': self.command_code,
#             'postback_message_code': self.postback_message_code,
#             'params': self.params,
#         }
#
