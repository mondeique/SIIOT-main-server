from rest_framework import serializers
from core.fields import URLResolvableUUIDField
from chats.models import ChatMessage
from chats.message_models import (
    TextChatMessageTmpl,
    ImageChatMessageTmpl,
)
from chats.profile_models import ChatSource


class ChatMessageUserDataSerializer(serializers.Serializer):
    """
    Input fields :
        - ['text', 'image_key', 'reply_token', 'postback_value']
    Output fields :
        - ['text', 'image_key', 'postback_parent', 'postback_value']
    Usage :
        input_data = {"text": ...}
        output_data = ChatMessageUserDataSerializer(data=input_data).data
    """
    text = serializers.CharField(allow_blank=True, required=False)
    image_key = URLResolvableUUIDField(allow_null=True, required=False)
    reply_token = serializers.UUIDField(write_only=True, allow_null=True, required=False)
    postback_parent = serializers.SerializerMethodField()
    postback_value = serializers.CharField(allow_null=True, required=False)
    source = serializers.SerializerMethodField()

    def get_postback_parent(self, data):
        reply_token = data.get('reply_token', None)
        if reply_token:
            return ChatMessage.objects.get(token=reply_token)
        return None

    def get_source(self, data):
        return ChatSource(user=self.context['request'].user)

    def convert(self):
        self.is_valid(raise_exception=True)
        chat_source = self.data['source']
        if self.data['text']:
            message = TextChatMessageTmpl(source=chat_source,
                                          text=self.data)
        elif self.data['image_key']:
            message = ImageChatMessageTmpl(source=chat_source,
                                           image_key=self.data['image_key'])
        else:
            raise Exception
        return message