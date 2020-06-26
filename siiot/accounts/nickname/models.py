from django.db import models


class FirstNickName(models.Model):
    """
    랜덤 닉네임 생성을 위해 만들었습니다. / 형용사
    """
    first_nickname = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_nickname


class LastNickName(models.Model):
    """
    랜덤 닉네임 생성을 위해 만들었습니다. / 명사
    """
    last_nickname = models.CharField(max_length=30, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.last_nickname
