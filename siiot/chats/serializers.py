# -*- encoding: utf-8 -*-
import datetime

import pytz
from rest_framework import serializers
from django.contrib.auth import get_user_model
# from chats.models import ChatRoom, SourceType, ChatMessage, ChatRoomParticipant, ChatRoomResult
from rest_framework.serializers import ModelSerializer

from chats.models import TestChatRoom, TestChatMessage
from core.cms import CMS
from core.fields import URLResolvableUUIDField

User = get_user_model()

#
# class ChatRoomSerializer(serializers.ModelSerializer):
#     owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
#     websocket_url = serializers.SerializerMethodField(read_only=True)
#     another_selves = serializers.SerializerMethodField()
#     version = serializers.IntegerField(required=False)
#
#     class Meta:
#         model = ChatRoom
#         fields = ('id', 'room_type', 'owner', 'websocket_url', 'another_selves', 'version')
#
#     def validate_room_type(self, value):
#         valid_values = ('contact', 'delivery')
#         if value not in valid_values:
#             raise serializers.ValidationError('invalid room type')
#         return value
#
#     def get_another_selves(self, instance):
#         return []
#
#     def get_websocket_url(self, instance):
#         if self.context:
#             cms = CMS(request=self.context['request'])
#         else:
#             cms = CMS()
#
#         domain = cms.get_key_name_config(key_name=CMS.CHAT_SERVER_DOMAIN)
#
#         # 새로운 채팅에서 사용하는 routing 규칙을 따름
#         return 'ws://{domain}/chats/{room_type}/{pk}/'.format(domain=domain,
#                                                              room_type=instance.room_type,
#                                                              pk=instance.id)
#
#     def create(self, validated_data):
#         instance = None
#         user = self.context['request'].user
#
#         # try returning existing instance
#         if validated_data['room_type'] == 'contact':
#             instance = ChatRoom.objects.filter(room_type='contact', contact__author=user).first()
#         if validated_data['room_type'] == 'delivery':
#             instance = ChatRoom.objects.filter(room_type='delivery', contact__author=user).first()
#
#         if not instance:
#             instance = super(ChatRoomSerializer, self).create(validated_data)
#         # participants
#         ChatRoomParticipant.objects.get_or_create(room=instance, user=user,
#                                                   defaults={'role': 'owner'})
#         return instance
#
#
# #
# # Message serializer
# #
# class ChatUserSerializer(serializers.ModelSerializer):
#     profile_image_url = serializers.SerializerMethodField(read_only=True)
#     is_staff = serializers.BooleanField()
#
#     class Meta:
#         model = User
#         fields = ('id', 'nickname', 'profile_image_url', 'is_staff')
#
#     def get_profile_image_url(self, obj):
#         return obj.profile_image_url
#
#
# class ChatBotSerializer(serializers.Serializer):
#     key = serializers.CharField()
#     nickname = serializers.CharField()
#     profile_image_url = serializers.CharField()
#
#
# class ChatSourceSerializer(serializers.Serializer):
#     type = serializers.SerializerMethodField()
#     user = ChatUserSerializer(source='source_user')
#     bot = ChatBotSerializer(source='source_bot')
#
#     def get_type(self, obj):
#         if obj.source_type == SourceType.USER:
#             return 'user'
#         else:
#             return 'bot'
#
#
# class ChatMessageReadSerializer(serializers.ModelSerializer):
#     type = serializers.CharField(source='get_message_type_display')
#     code = serializers.CharField()
#     source = ChatSourceSerializer()
#     template = serializers.JSONField()
#     text = serializers.CharField()
#     preview_image_url = serializers.CharField()  # FIXME: optimize
#     original_content_url = serializers.CharField()
#     caption = serializers.CharField()
#     duration = serializers.IntegerField()
#     uri = serializers.CharField()
#     token = serializers.CharField()
#     extras = serializers.JSONField()
#     created_at = serializers.DateTimeField()
#     updated_at = serializers.DateTimeField()
#     room_id = serializers.IntegerField(source='room.id')
#
#     def to_representation(self, instance):
#         """
#         Copy-paste of rest_framework.serializers.Serializer.to_representation
#         """
#         from collections import OrderedDict
#         from rest_framework.relations import PKOnlyObject
#
#         ret = OrderedDict()
#         fields = self._readable_fields
#
#         for field in fields:
#             try:
#                 attribute = field.get_attribute(instance)
#             except Exception:
#                 # (MODIFIED) skip field if any exception (including AttributeError) occurs
#                 continue
#
#             check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
#             # (MODIFIED) skip serializing "None" and blank values
#             if check_for_none is None:
#                 # ret[field.field_name] = None
#                 pass
#             else:
#                 # ret[field.field_name] = field.to_representation(attribute)
#                 val = field.to_representation(attribute)
#                 if val:
#                     ret[field.field_name] = val
#
#         try:
#             ret['str_created_at'] = instance.created_at.astimezone(pytz.timezone('Asia/Seoul')).strftime(
#                 '%Y.%m.%d %H:%M:%S')
#         except:
#             ret['str_created_at'] = ''
#         return ret
#
#     class Meta:
#         model = ChatMessage
#         fields = (
#             'id',
#             'type',
#             'room_id',
#             'text',
#             'code',
#             'preview_image_url',
#             'original_content_url',
#             'caption',
#             'uri',
#             'duration',
#
#             'source',
#
#             'template',
#
#             'token',
#             'extras',
#             'command',
#
#             'object_id',
#
#             'created_at',
#             'updated_at',
#         )
#
#     def get_room_id(self, obj):
#         try:
#             return obj.room.id
#         except Exception as e:
#             return None
#
#
# class ChatMessageFullReadSerializer(ChatMessageReadSerializer):
#     target_user = ChatUserSerializer()
#
#     class Meta:
#         model = ChatMessage
#         fields = ChatMessageReadSerializer.Meta.fields + ('target_user',)
#
#
# class ChatMessageWriteSerializer(serializers.ModelSerializer):
#     """
#     ChatMessage object를 생성할 때 사용합니다. (ex: ChatMessageTmpl.save)
#     """
#     room = serializers.PrimaryKeyRelatedField(queryset=ChatRoom.objects.all())
#     text = serializers.CharField(allow_blank=True, required=False)
#     code = serializers.CharField(allow_blank=True, required=False)
#     image_key = URLResolvableUUIDField(allow_null=True, required=False)
#     content_url = serializers.CharField(allow_blank=True, required=False)
#     caption = serializers.CharField(allow_blank=True, required=False)
#     uri = serializers.CharField(allow_blank=True, required=False)
#     version = serializers.HiddenField(default=1)
#
#     source_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
#                                                      allow_null=True, required=False)
#     source_bot_key = serializers.CharField(allow_blank=True, required=False)
#
#     template = serializers.JSONField(allow_null=True, required=False)
#
#     target_user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(),
#                                                      allow_null=True, required=False)
#     is_hidden = serializers.BooleanField(default=False)
#
#     postback_parent = serializers.PrimaryKeyRelatedField(queryset=ChatMessage.objects.all(),
#                                                          allow_null=True, required=False)
#     postback_value = serializers.CharField(allow_blank=True, required=False)
#     extras = serializers.JSONField(allow_null=True, required=False)
#
#     object_id = serializers.IntegerField(allow_null=True, required=False)
#
#     client_handler_version = serializers.IntegerField(allow_null=True, required=False)
#     target_handler_version = serializers.IntegerField(allow_null=True, required=False)
#
#     class Meta:
#         model = ChatMessage
#         fields = (
#             'message_type',
#             'room',
#             'text',
#             'code',
#             'image_key',
#             'content_url',
#             'caption',
#             'uri',
#             'version',
#
#             'source_type',
#             'source_user',
#             'source_bot_key',
#
#             'template',
#
#             'target_user',
#             'is_hidden',
#
#             'token',
#             'postback_parent',
#             'postback_value',
#             'extras',
#
#             'object_id',
#
#             'client_handler_version',
#             'target_handler_version',
#         )
#
#
# class ChatRoomResultSerializer(serializers.ModelSerializer):
#     user = serializers.HiddenField(default=serializers.CurrentUserDefault())
#
#     class Meta:
#         model = ChatRoomResult
#         fields = (
#             'user', 'result', 'elapsed'
#         )


class MessageModelSerializer(ModelSerializer): # 챗 룸에 저장 ->
    room = serializers.CharField()

    def create(self, validated_data):
        print(validated_data)
        room = TestChatRoom.objects.get(id=int(validated_data['room']))

        msg = TestChatMessage(room=room,
                              text=validated_data['text'],
                              message_type=1,
                              source_type=1)
        msg.save()
        return msg

    class Meta:
        model = TestChatMessage
        fields = ('text', 'room')


class MessageRetrieveSerializer(ModelSerializer):
    user = serializers.SerializerMethodField()
    recipient = serializers.SerializerMethodField()

    class Meta:
        model = TestChatMessage
        fields = ('id', 'user', 'text', 'recipient', 'created_at')

    def get_user(self, obj):
        return obj.room.buyer.nickname

    def get_recipient(self, obj):
        return obj.room.seller.nickname

