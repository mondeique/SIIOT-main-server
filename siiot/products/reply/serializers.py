from rest_framework import serializers, exceptions

from core.utils import get_age_fun
from products.models import Product
from products.reply.models import ProductQuestion, ProductAnswer


class ProductQuestionCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductQuestion
        fields = '__all__'


class ProductQuestionRetrieveSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()
    edit_possible = serializers.SerializerMethodField()

    class Meta:
        model = ProductQuestion
        fields = ['id', 'profile_img', 'product', 'text', 'age', 'edit_possible']

    def get_age(self, obj):
        return get_age_fun(obj)

    def get_profile_img(self, obj):
        user = obj.user
        if hasattr(user, 'profile'):
            return user.profile.profile_img.url
        return None

    def get_edit_possible(self, obj):
        return not obj.answers.exists()


# answer
class ProductAnswerCreateSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = ProductAnswer
        fields = '__all__'


class ProductAnswerRetrieveSerializer(serializers.ModelSerializer):
    age = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()

    class Meta:
        model = ProductAnswer
        fields = ['id', 'question', 'nickname', 'text', 'age']

    def get_age(self, obj):
        return get_age_fun(obj)

    def get_nickname(self, obj):
        user = obj.user
        return user.nickname

# replies list
class ProductRepliesSerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    edit_possible = serializers.SerializerMethodField()

    class Meta:
        model = ProductQuestion
        fields = ['id', 'profile_img', 'product', 'text', 'age','nickname', 'edit_possible', 'answers']

    def get_age(self, obj):
        return get_age_fun(obj)

    def get_profile_img(self, obj):
        user = obj.user
        if hasattr(user, 'profile'):
            return user.profile.profile_img.url
        return None

    def get_nickname(self, obj):
        user = obj.user
        return user.nickname

    def get_edit_possible(self, obj):
        return not obj.answers.exists()

    def get_answers(self, obj):
        answers = obj.answers.all()
        if answers.exists():
            return ProductAnswerRetrieveSerializer(answers, many=True).data
        return None

class ProductReplySerializer(serializers.ModelSerializer):
    answers = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    profile_img = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    edit_possible = serializers.SerializerMethodField()

    class Meta:
        model = ProductQuestion
        fields = ['id', 'profile_img', 'nickname', 'product', 'text', 'age', 'edit_possible', 'answers']

    def get_age(self, obj):
        return get_age_fun(obj)

    def get_profile_img(self, obj):
        user = obj.user
        if hasattr(user, 'profile'):
            return user.profile.profile_img.url
        return None

    def get_nickname(self, obj):
        user = obj.user
        return user.nickname

    def get_edit_possible(self, obj):
        return not obj.answers.exists()

    def get_answers(self, obj):
        if obj.answers.exists():
            answers = obj.answers.first()
            return ProductAnswerRetrieveSerializer(answers).data
        return None
