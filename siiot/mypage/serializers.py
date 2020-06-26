from rest_framework import serializers
from django.contrib.auth import get_user_model

from mypage.models import DeliveryPolicy


class SimpleSellerInfoSerializer(serializers.ModelSerializer):
    profile_img = serializers.SerializerMethodField()
    star_rating = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = ['id', 'profile_img', 'nickname', 'star_rating']

    def get_profile_img(self, obj):
        user = obj
        if hasattr(user, 'profile'):
            return user.profile.profile_img.url
        return None

    def get_star_rating(self, obj):
        # todo: review 만들고 rating 계산
        return 5.0


class DeliveryPolicyInfoSerializer(serializers.ModelSerializer):

    class Meta:
        model = DeliveryPolicy
        fields = '__all__'
