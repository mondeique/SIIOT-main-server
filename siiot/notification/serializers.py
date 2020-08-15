from rest_framework import serializers
from .models import Notification, NotificationUserLog


class NotificationSerializer(serializers.ModelSerializer):
    queryset = Notification.objects.all()
    read_at = serializers.SerializerMethodField()
    deleted_at = serializers.SerializerMethodField()
    # extras = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            'id', 'action', 'title', 'content', 'read_at', 'target', 'created_at', 'link', 'image', 'icon',
            'big_image', 'deleted_at')
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

    # def get_extras(self, obj):
    #     try:
    #         user = self.context['request'].user
    #         user_log = obj.user_logs.filter(user=user).first()
    #         return user_log.extras
    #     except:
    #         user_log = obj.user_logs.first()
    #         if user_log:
    #             return user_log.extras
    #         else:
    #             return {}


class NotificationListSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    link = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = NotificationUserLog
        fields = ['title', 'content', 'icon', 'link', 'created_at']

    def get_title(self, obj):
        noti = obj.notification
        return noti.title

    def get_content(self, obj):
        noti = obj.notification
        return noti.content

    def get_icon(self, obj):
        noti = obj.notification
        return noti.icon

    def get_link(self, obj):
        noti = obj.notification
        return noti.link

    def get_created_at(self, obj):
        created_at = obj.created_at
        created_at = created_at.strftime('%y/%m/%d %H:%M')
        return created_at
