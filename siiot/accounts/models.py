from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


def img_directory_path_profile(instance, filename):
    return 'user/{}/profile/{}'.format(instance.user.nickname, filename)


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
    phone = models.CharField(max_length=20, blank=True, null=True,
                             help_text="탈퇴 후 재 가입 시 같은 번호로 사용할 수 있으므로 unique 설정하지 않음")
    uid = models.UUIDField(default=None, blank=True, null=True, unique=True,
                           help_text="phone 대신 USERNAME_FIELD를 대체할 field입니다.")
    USERNAME_FIELD = 'uid'
    REQUIRED_FIELDS = ['nickname']

    objects = UserManager()
    is_active = models.BooleanField(default=True, help_text="탈퇴/밴 시 is_active = False")
    is_banned = models.BooleanField(default=False, help_text="밴 여부")
    is_staff = models.BooleanField(default=False, help_text="super_user와의 권한 구분을 위해서 새로 만들었습니다. 일반적 운영진에게 부여됩니다.")

    created_at = models.DateTimeField(auto_now_add=True)
    quit_at = models.DateTimeField(blank=True, null=True, default=None)

    email = models.EmailField(max_length=100, unique=True, db_index=True, blank=True, null=True,
                              help_text="운영진 staff page에서 로그인 시 사용합니다.")

    def __str__(self):
        if self.is_anonymous:
            return 'anonymous'
        if self.is_staff:
            return '[staff] {}'.format(self.email)
        if self.nickname:
            return self.nickname
        return self.phone


class PhoneConfirm(models.Model):
    """
    회원가입/ 비밀번호 변겅 핸드폰 인증에 사용하는 모델입니다. <TODO: 판매 User 본인인증에 관해서는 따로 만들어야 합니다.>
    User를 생성하기 전에 핸드폰 인증이 되어야 추가정보(비밀번호, 닉네임)와 같이 POST를 보낼 수 있습니다.
    인증번호를 받는 제한시간은 없습니다.
    is_confirmed 는 서버에서 참고하기 위한 정보입니다. 실제 데이터(phone, pw, nickname)를 client 보냈을 때 is_confirmed를 참고만 합니다.
    """

    SIGN_UP = 1
    RESET_PASSWORD = 2

    KINDS = (
        (SIGN_UP, '회원가입'),
        (RESET_PASSWORD, '비밀번호 변경')
    )

    phone = models.CharField(max_length=20)
    certification_number = models.CharField(max_length=4)
    kinds = models.IntegerField(choices=KINDS, default=1)
    temp_key = models.UUIDField(null=True, help_text="같은 인증번호를 보내기 위해 사용함.")
    is_confirmed = models.BooleanField(default=False, help_text='인증에 사용되었던 번호 여부')
    created_at = models.DateTimeField(auto_now_add=True)


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="profile", on_delete=models.CASCADE)
    profile_img = models.ImageField(upload_to=img_directory_path_profile,
                                    default='default_profile.png')
