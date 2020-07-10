from rest_framework import serializers
from chat.models import ChatRoom

class ChatRoomSerializer(serializers.ModelSerializer):
    is_buyer = serializers.SerializerMethodField()
    is_seller = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = ['id', 'deal', 'is_buyer', 'is_seller', 'unread_count', 'created_at']

    def get_is_buyer(self, obj):
        user = self.context['request'].user
        deal = obj.deal
        if deal.buyer == user:
            return True
        return False

    def get_is_seller(self, obj):
        user = self.context['request'].user
        deal = obj.deal
        if deal.seller == user:
            return True
        return False

    def get_unread_count(self, obj):
        room = obj
        messages = room.messages.filter(is_read=False)
        return messages.count()