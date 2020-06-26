from django.contrib.auth import (
    login as django_login,
    logout as django_logout,
    get_user_model)
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated

# Create your views here.
from accounts.models import User, PhoneConfirm
from accounts.serializers import LoginSerializer, SignupSerializer, CredentialException, NicknameSerializer, \
    ResetPasswordSerializer
from accounts.sms.signature import simple_send
from accounts.sms.utils import SMSManager
from accounts.utils import create_token, set_random_nickname


class AccountViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = [AllowAny, ]
    queryset = User.objects.filter(is_active=True)
    token_model = Token

    def get_serializer_class(self):
        if self.action == 'signup':
            serializer = SignupSerializer
        elif self.action == 'reset_pw':
            serializer = ResetPasswordSerializer
        elif self.action == 'login':
            serializer = LoginSerializer
        else:
            serializer = super(AccountViewSet, self).get_serializer_class()
        return serializer

    @action(methods=['get'], detail=False)
    def check_userinfo(self, request):
        """
        스플래시 화면에서 유저가 자동로그인이 가능하도록 해당 유저가 가지고 있는 토큰의 유효성을 판단하는 API
        추가로 유저의 환불계좌 입력 유무에 따라 업로드 시 client 에서 띄워주는 페이지가 다름
        api: POST accounts/v1/check_userinfo/
        :param request: header token or not
        :return:
        200 : 해당 토큰을 가진 유저가 존재할 때
        401 : 해당 토큰을 가진 유저가 존재하지 않거나 토큰을 담아서 주지 않았을 때
        """
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if request.user:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

    @action(methods=['post'], detail=False)
    def signup(self, request, *args, **kwargs):
        """
        회원가입시 사용하는 api 입니다.
        sms 인증이 완료될 때 return 된 phone, temp_key에 + password 을 입력받습니다.
        temp_key를 활용하여 외부 api로 signup을 방지하였습니다.
        nickname의 경우 자동으로 random nickname이 부여되고, 회원가입 이후 nickname을 입력하면 update가 됩니다.
        api: POST accounts/v1/signup/

        :return:
        400 : bad request
        401 : temp_key가 유효하지 않을 때
        201 : created
        """
        data = request.data.copy()

        # check is confirmed (temp key로서 외부의 post 막음)
        temp_key = data.get('temp_key')
        if not temp_key:
            return Response("No temp key", status=status.HTTP_400_BAD_REQUEST)
        temp_key = data.pop('temp_key')
        phone_confirm = PhoneConfirm.objects.get(temp_key=temp_key)
        if not phone_confirm.is_confirmed:
            return Response("Unconfirmed Phone number", status=status.HTTP_401_UNAUTHORIZED)
        if phone_confirm.phone != data.get("phone"):
            return Response("Not match phone number & temp key", status=status.HTTP_401_UNAUTHORIZED)

        # user 생성
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # default random nickname
        user.nickname = set_random_nickname(get_user_model())
        user.save()

        token = create_token(self.token_model, user)

        return Response({'token': token.key}, status=status.HTTP_201_CREATED)

    def _login(self):
        user = self.serializer.validated_data['user']
        setattr(user, 'backend', 'django.contrib.auth.backends.ModelBackend')
        django_login(self.request, user)
        # loginlog_on_login(request=self.request, user=user)

    @action(methods=['post'], detail=False)
    def login(self, request, *args, **kwargs):
        """
        api: POST accounts/v1/login/

        """
        try:
            self.serializer = self.get_serializer(data=request.data)
            self.serializer.is_valid(raise_exception=True)
            self._login()
            token = self.serializer.validated_data['token']
        except CredentialException:
            return Response({"non_field_errors": ['Unable to log in with provided credentials.']},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'token': token}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False, url_name='logout')
    def logout(self, request):
        """
        api: POST accounts/v1/logout/

        :return: code, status
        """
        try:
            request.user.auth_token.delete()
        except (AttributeError, ObjectDoesNotExist):
            key = request.headers['Authorization']
            if key:
                token = Token.objects.get(key=key.split(' ')[1])
                token.delete()
        if getattr(settings, 'REST_SESSION_LOGIN', True):
            django_logout(request)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def reset_pw(self, request, *args, **kwargs):
        """
        비밀번호 재설정에 사용하는 api 입니다.
        sms 인증이 완료될 때 return 된 phone, temp_key에 + password 을 입력받습니다.
        temp_key를 활용하여 외부 api로 signup을 방지하였습니다.
        nickname의 경우 자동으로 random nickname이 부여되고, 회원가입 이후 nickname을 입력하면 update가 됩니다.

        api: POST accounts/v1/reset_pw/

        :return:
        400 : bad request
        401 : temp_key가 유효하지 않을 때
        201 : created
        """
        data = request.data.copy()

        # check is confirmed (temp key로서 외부의 post 막음)
        temp_key = data.get('temp_key')
        if not temp_key:
            return Response("No temp key", status=status.HTTP_400_BAD_REQUEST)

        temp_key = data.pop('temp_key')
        phone_confirm = PhoneConfirm.objects.get(temp_key=temp_key)
        if not phone_confirm.is_confirmed:
            return Response("Unconfirmed phone number", status=status.HTTP_401_UNAUTHORIZED)
        if phone_confirm.phone != data.get("phone"):
            return Response("Not match phone number & temp key", status=status.HTTP_401_UNAUTHORIZED)

        phone = data.pop('phone')
        user = User.objects.filter(phone=phone, is_active=True)

        if user.count() == 0:
            return Response("User does not exist", status=status.HTTP_400_BAD_REQUEST)

        user = user.last()

        # password reset(update) 생성
        serializer = self.get_serializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        token = create_token(self.token_model, user)

        return Response({'token': token.key}, status=status.HTTP_206_PARTIAL_CONTENT)


class NicknameViewSet(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated, ]
    serializer_class = NicknameSerializer
    queryset = User.objects.filter(is_active=True)

    @action(methods=['post'], detail=False)
    def register(self, request, *args, **kwargs):
        """
        User 회원가입시 nickname을 자동 생성 한 이후, NicknameViewSet 을 사용하여 nickname을 update 합니다.
        My page 에서 닉네임 업데이트시에도 사용합니다.

        api: POST accounts/v1/nickname/register/
        """
        user = request.user

        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        nickname = serializer.data['nickname']

        # check duplicate nickname
        if User.objects.filter(nickname=nickname).exists():
            return Response(status=status.HTTP_409_CONFLICT)

        # nickname save
        serializer.save()

        return Response(status=status.HTTP_206_PARTIAL_CONTENT)

    @action(['get'], detail=False, permission_classes=[AllowAny])
    def random(self, request, *args, **kwargs):
        """
        [PEPUP-226] 2020.06.11
        api: GET accounts/v1/nickname/random/
        """
        nickname = set_random_nickname(get_user_model())
        return Response({'nickname': nickname})


class SMSViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny, ]
    serializer_class = None

    @action(methods=['post'], detail=False)
    def signup(self, request, *args, **kwargs):
        """
        회원가입 시 인증번호를 받는 api 입니다.
        body 에 phone 을 담아 보내주기만 하면 됩니다.

        api: POST accounts/v1/send_sms/signup/

        :return : temp_key (이를 활용하여 재발급에 사용)
        400 : bad request -> phone 을 보내지 않았을 때
        401 : 강제 밴 처리 당한 유저
        409 : 이미 가입 내역이 존재
        500 : (1) client에서 data 양식에 맞지 않게 요청시, (2) send error
        """
        data = request.data.copy()
        phone = data.get('phone')

        if not phone:
            return Response("No phone number", status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone=phone, is_banned=True).exists():
            return Response("User is banned", status=status.HTTP_401_UNAUTHORIZED) # banned user
        elif User.objects.filter(phone=phone, is_active=True).exists():
            return Response("Phone number already exists", status=status.HTTP_409_CONFLICT) # already exists

        sms_manager = SMSManager()
        sms_manager.set_content()
        sms_manager.create_instance(phone=phone, kind=PhoneConfirm.SIGN_UP)
        print(sms_manager.temp_key)
        if not sms_manager.send_sms(phone=phone):
            return Response("Failed send sms", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'temp_key': sms_manager.temp_key}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def reset_pw(self, request, *args, **kwargs):
        """
        비밀번호 재설정시 인증번호를 받는 api 입니다.
        body 에 phone 을 담아 보내주기만 하면 됩니다.

        api: POST accounts/v1/send_sms/reset_pw/

        :return : temp_key (이를 활용하여 재발급에 사용)
        400 : bad request -> phone 을 보내지 않았을 때
        401 : 강제 밴 처리 당한 유저
        204 : 가입 내역이 없음
        500 : (1) client에서 data 양식에 맞지 않게 요청시, (2) send error
        """
        data = request.data.copy()
        phone = data.get('phone')

        if not phone:
            return Response("No phone number", status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone=phone, is_banned=True).exists():
            return Response("User is banned", status=status.HTTP_401_UNAUTHORIZED)  # banned user
        elif not User.objects.filter(phone=phone, is_active=True).exists():
            return Response("User does not exists", status=status.HTTP_204_NO_CONTENT)  # no user

        sms_manager = SMSManager()
        sms_manager.set_content()
        sms_manager.create_instance(phone=phone, kind=PhoneConfirm.RESET_PASSWORD)

        if not sms_manager.send_sms(phone=phone):
            return Response("Failed send sms", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'temp_key': sms_manager.temp_key}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def resend(self, request, *args, **kwargs):
        """
        인증번호 재발급에 사용하는 api 입니다.
        body 에 temp_key를 담아 보내주기만 하면 됩니다.

        api: POST accounts/v1/send_sms/resend/

        :return
        400 : bad request -> temp_key 에 데이터가 존재하지 않을 때
        404 : not found -> 잘못된 temp_key를 보냈을 때
        500 :  (1) client에서 data 양식에 맞지 않게 요청시, (2) send error
        """
        data = request.data.copy()
        temp_key = data.get('temp_key')

        if not temp_key:
            return Response("No temp key", status=status.HTTP_400_BAD_REQUEST)

        if not PhoneConfirm.objects.filter(temp_key=temp_key).exists():
            return Response("Invalid temp key", status=status.HTTP_404_NOT_FOUND)

        obj = PhoneConfirm.objects.filter(temp_key=temp_key).last()
        certification_number = obj.certification_number
        phone = obj.phone

        if not simple_send(certification_number, phone):
            return Response("Failed send sms", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def confirm(self, request, *args, **kwargs):
        """
        인증번호를 확인하는 api 입니다.
        body 에 phone 과 key 를 담아 보내야 합니다.
        return 400 시 재전송이 아닌, 이전페이지(핸드폰 번호 입력)로 이동하여 새로운 코드를 발급해야 합니다.

        api: POST accounts/v1/send_sms/confirm/

        :return : phone, temp_key
        400 : bad request -> (1) phone 또는 key 가 없을 때, (2) 해당 key가 이미 인증에 사용된 key 일 때
        404 : not found -> key 가 맞지 않을 때
        """
        data = request.data.copy()
        phone = data.get('phone')
        key = str(data.get('key'))  # certification number

        if not phone or not key:
            return Response("No phone number or No key", status=status.HTTP_400_BAD_REQUEST)

        obj = PhoneConfirm.objects.filter(phone=phone).last()
        if obj.is_confirmed:  # already used key
            return Response("Invalid key: Already used to confirm", status=status.HTTP_400_BAD_REQUEST)

        if obj.certification_number != key:
            return Response("Not match key & server key", status=status.HTTP_404_NOT_FOUND)
        print(obj.certification_number, type(obj.certification_number))
        print(key, type(key))
        obj.is_confirmed = True
        obj.save()

        return Response({'phone': obj.phone, 'temp_key': obj.temp_key}, status=status.HTTP_200_OK)

