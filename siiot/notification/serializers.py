from rest_framework import serializers
from .models import Notification, SIIOTGCMDevice


class NotificationSerializer(serializers.ModelSerializer):
    queryset = Notification.objects.all()
    read_at = serializers.SerializerMethodField()
    deleted_at = serializers.SerializerMethodField()
    extras = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            'id', 'action', 'title', 'content', 'read_at', 'target', 'created_at', 'link', 'image', 'icon',
            'big_image', 'deleted_at', 'extras')
        read_only_field = ('created_at')

    def get_read_at(self, obj):
        try:
            user = self.context['request'].user
            user_log = obj.user_logs.filter(user=user).first()
            return user_log.read_at
        except:
            return None

    def get_deleted_at(self, obj):
        try:
            user = self.context['request'].user
            user_log = obj.user_logs.filter(user=user).first()
            return user_log.deleted_at
        except:
            return None

    def get_extras(self, obj):
        try:
            user = self.context['request'].user
            user_log = obj.user_logs.filter(user=user).first()
            return user_log.extras
        except:
            user_log = obj.user_logs.first()
            if user_log:
                return user_log.extras
            else:
                return {}