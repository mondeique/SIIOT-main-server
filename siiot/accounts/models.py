from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


def img_directory_path_profile(instance, filename):
    return 'user/{}/profile/{}'.format(instance.user.email, filename)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, password, nickname, phone, **kwargs):
        if not phone:
            raise ValueError('핸드폰 번호를 입력해주세요')
        user = self.model(nickname=nickname, phone=phone, **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, nickname, phone, password=None, **kwargs):
        kwargs.setdefault('is_staff', False)
        kwargs.setdefault('is_superuser', False)
        return self._create_user(password, nickname, phone, **kwargs)

    def create_superuser(self, password, nickname, phone, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)

        if kwargs.get('is_staff') is not True:
            raise ValueError('superuser must have is_staff=True')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('superuser must have is_superuser=True')
        return self._create_user(password, nickname, phone, **kwargs)


class User(AbstractUser):
    # username = None
    nickname = models.CharField(max_length=30, unique=True, null=True, verbose_name='nickname')
    phone = models.CharField(max_length=19, unique=True, null=True, help_text='숫자만 입력해주세요')
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['nickname']

    objects = UserManager()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    quit_at = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self):
        if self.is_anonymous:
            return 'anonymous'
        if self.nickname:
            return self.nickname
        return self.phone


class PhoneConfirm(models.Model):
    """
    회원가입/ 비밀번호 변겅 핸드폰 인증에 사용하는 모델입니다. <TODO: User 본인인증에 관해서는 따로 만들어야 합니다.>
    User를 생성하기 전에 핸드폰 인증이 되어야 추가정보(비밀번호, 닉네임)와 같이 POST를 보낼 수 있습니다.
    인증번호를 받는 제한시간은 30초 입니다. (서버 부하 방지용. 30초 간격으로 여러번 클릭 가능하고, 가장 마지막 인증번호로 인증이 됩니다.)
    is_confirmed 는 서버에서 참고하기 위한 정보일 뿐 실제 데이터는 client 가 서버에서 발행한 temp_key 데이터를 보내주어야 합니다.
    """

    SIGN_UP = 1
    RESET_PASSWORD = 2

    KINDS = (
        (SIGN_UP, '회원가입'),
        (RESET_PASSWORD, '비밀번호 변경')
    )

    phone = models.CharField(max_length=20)
    certification_number = models.CharField(max_length=6)
    kinds = models.IntegerField(choices=KINDS, default=1)
    temp_key = models.UUIDField(help_text="인증완료되었다는 임시 키, 마지막 post에서 해당 키를 클라에서 받아야 프로세스 완료")
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to=img_directory_path_profile,
                                    default='default_profile.png')
