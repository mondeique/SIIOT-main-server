from django.db import models


class FirstNickName(models.Model):
    """
    랜덤 닉네임 생성을 위해 만들었습니다.
    """
    first_nickname = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LastNickName(models.Model):
    """
    랜덤 닉네임 생성을 위해 만들었습니다.
    """
    Last_nickname = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
