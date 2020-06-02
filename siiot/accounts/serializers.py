from django.conf import settings
from django.db.models import Avg
from rest_framework import serializers, exceptions
from django.contrib.auth import authenticate
from .models import User, PhoneConfirm, Profile
from rest_framework.authtoken.models import Token
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("password", "nickname")

    def validate(self, attrs):
        phone = attrs.get('phone')
        # Did we get back an active user?
        if User.objects.filter(phone=phone):
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise exceptions.ValidationError(msg)

        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            nickname=validated_data['nickname'],
            phone=validated_data['phone']
        )
        user.set_password(validated_data['password'])
        user.save()

        return user

    def update(self, instance, validated_data):
        if validated_data.get('phone'):
            instance.phone = validated_data['phone']
        if validated_data.get('nickname'):
            instance.nickname = validated_data['nickname']
        if validated_data.get('password'):
            instance.set_password(validated_data['password'])
        instance.save()
        # 유저 생성될 때 profile instance 생성.
        # Profile.objects.get_or_create(user=instance)
        return instance


class PhoneConfirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneConfirm
        fields = '__all__'

    # 세션완료, 30초
    def timeout(self, instance):
        if not instance.is_confirmed:
            if timezone.now().timestamp() - instance.created_at.timestamp() >= 30:
                instance.delete()
                return True
        return False


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'})

    def authenticate(self, **kwargs):
        return authenticate(self.context['request'], **kwargs)

    def _validate_email(self, email, password):
        user = None
        if email and password:
            user = self.authenticate(email=email, password=password)
        else:
            msg = _('Must include "email" and "password".')
            raise exceptions.ValidationError(msg)

        return user

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = self._validate_email(email, password)

        # Did we get back an active user?
        if user:
            if not user.is_active:
                msg = _('User account is disabled.')
                raise exceptions.ValidationError(msg)
        else:
            msg = _('Unable to log in with provided credentials.')
            raise exceptions.ValidationError(msg)

        attrs['user'] = user
        return attrs


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ('key',)


class ThumbnailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['thumbnail_img']

    def get_thumbnail_img(self, obj):
        thumbnail_img = obj.thumbnail_img
        if thumbnail_img:
            return thumbnail_img.url
        return "/media/test.png"


class UserSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    review_score = serializers.SerializerMethodField()
    sold = serializers.SerializerMethodField()
    followers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'profile', 'review_score', 'sold', 'followers']

    def get_sold(self, obj):
        return obj.product_set.filter(sold=True).count()

    def get_review_score(self, obj):
        if obj.received_reviews.first():
            score = obj.received_reviews.all().values('satisfaction').\
                annotate(score=Avg('satisfaction')).values('score')[0]['score']
            return score
        return 0.0

    def get_followers(self, obj):
        return obj._to.count()

    def get_profile(self, obj):
        return obj.profile.profile_img_url

    # def get_profile(self, obj):
    #     if hasattr(obj.socialaccount_set.last(), 'extra_data'):
    #         social_profile_img = obj.socialaccount_set.last().extra_data['properties'].get('profile_image')
    #         return {"thumbnail_img": social_profile_img}
    #     try:
    #         profile = obj.profile
    #         return ThumbnailSerializer(profile).data
    #     except:
    #          return {"thumbnail_img": "{}img/profile_default.png".format(settings.STATIC_ROOT)}


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['user', 'thumbnail_img', 'introduce']


class CommonSerializer(serializers.Serializer):
    totalCount = serializers.IntegerField()
    currentPage = serializers.IntegerField()


class SearchAddrSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['zipNo', 'Addr']


class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id','phone','name','zipNo', 'Addr','detailAddr', 'recent']


class KakaoSerializer(serializers.Serializer):
    id = serializers.CharField()
    # properties =


class ChatUserInfoSerializer(serializers.ModelSerializer):
    profile_img = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'nickname', 'profile_img']

    def get_profile_img(self, obj):
        profile = obj.profile
        return profile.profile_img_url