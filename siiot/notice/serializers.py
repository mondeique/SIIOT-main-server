import datetime

from rest_framework import serializers

from notice.models import Notice


class NoticeListSerializer(serializers.ModelSerializer):
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = ['id', 'title', 'uploaded_at']

    def get_uploaded_at(self, obj):
        updated_at = obj.updated_at
        reformat_updated_at = datetime.datetime.strftime(updated_at, '%Y-%m-%d')
        return reformat_updated_at


class NoticeRetrieveSerializer(serializers.ModelSerializer):
    uploaded_at = serializers.SerializerMethodField()

    class Meta:
        model = Notice
        fields = ['id', 'title', 'content', 'uploaded_at']

    def get_uploaded_at(self, obj):
        updated_at = obj.updated_at
        reformat_updated_at = datetime.datetime.strftime(updated_at, '%Y-%m-%d')
        return reformat_updated_at
