
from django.contrib.auth import (
    login as django_login,
    logout as django_logout
)
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
from accounts.serializers import LoginSerializer, SignupSerializer
from accounts.sms.signature import simple_send
from accounts.sms.utils import SMSManager
from accounts.utils import create_token


class AccountViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    permission_classes = (AllowAny, )
    queryset = User.objects.filter(is_active=True)
    token_model = Token

    def get_serializer_class(self):
        if self.action == 'signup':
            serializer = SignupSerializer
        elif self.action == 'login':
            serializer = LoginSerializer
        elif self.action == 'reset_password':
            serializer = None
        else:
            serializer = super(AccountViewSet, self).get_serializer_class()
        return serializer

    @action(methods=['post'], detail=False)
    def signup(self, request, *args, **kwargs):
        data = request.data.copy()

        # check is confirmed (temp key로서 외부의 post 막음)
        temp_key = data.get('temp_key')
        if not temp_key:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        temp_key = data.pop('temp_key')
        phone_confirm = PhoneConfirm.objects.get(temp_key=temp_key)
        if not phone_confirm.is_confirmed:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data=data)

        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()

        # if user set nickname
        nickname = data.get('nickname')
        if nickname:
            user.nickname = nickname
            user.save()

        token = create_token(self.token_model, user)

        return Response({'token': token.key}, status=status.HTTP_201_CREATED)


class SignupSMSViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    serializer_class = None

    @action(methods=['post'], detail=False)
    def send(self, request, *args, **kwargs):
        """
        회원가입 시 인증번호를 받는 api 입니다.
        body 에 phone 을 담아 보내주기만 하면 됩니다.
        :return
        400 : bad request -> phone 을 보내지 않았을 때
        401 : 강제 밴 처리 당한 유저
        409 : 이미 가입 내역이 존재
        500 : (1) client에서 data 양식에 맞지 않게 요청시, (2) send error
        """
        data = request.data.copy()
        phone = data['phone']

        if not phone:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(phone=phone, is_banned=True):
            return Response(status=status.HTTP_401_UNAUTHORIZED) # banned user
        elif User.objects.filter(phone=phone, is_active=True):
            return Response(status=status.HTTP_409_CONFLICT) # already exists

        sms_manager = SMSManager()
        sms_manager.set_content()
        sms_manager.create_instance(phone=phone, kind=PhoneConfirm.SIGN_UP)

        if not sms_manager.send_sms(phone=phone):
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'temp_key': sms_manager.temp_key}, status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def resend(self, request, *args, **kwargs):
        """
        인증번호 재발급에 사용하는 api 입니다.
        body 에 temp_key를 담아 보내주기만 하면 됩니다.
        :return:
        400 : bad request -> temp_key 에 데이터가 존재하지 않을 때
        404 : not found -> 잘못된 temp_key를 보냈을 때
        500 :  (1) client에서 data 양식에 맞지 않게 요청시, (2) send error
        """
        data = request.data.copy()
        temp_key = data['temp_key']

        if not temp_key:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if not PhoneConfirm.objects.filter(temp_key=temp_key):
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj = PhoneConfirm.objects.filter(temp_key=temp_key).last()
        certification_number = obj.certification_number
        phone = obj.phone

        if not simple_send(certification_number, phone):
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(status=status.HTTP_200_OK)

    @action(methods=['post'], detail=False)
    def confirm(self, request, *args, **kwargs):
        """
        인증번호를 확인하는 api 입니다.
        body 에 phone 과 key 를 담아 보내야 합니다.
        return 400 시 재전송이 아닌, 이전페이지(핸드폰 번호 입력)로 이동하여 새로운 코드를 발급해야 합니다.
        :return
        400 : bad request -> (1) phone 또는 key 가 없을 때, (2) 해당 key가 이미 인증에 사용된 key 일 때
        404 : not found -> key 가 맞지 않을 때
        """
        data = request.data.copy()
        phone = data['phone']
        key = str(data['key'])  # certification number

        if not phone or not key:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        obj = PhoneConfirm.objects.filter(phone=phone).last()
        if obj.is_confirmed:  # already used key
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if obj.certification_number != key:
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj.is_confirmed = True
        obj.save()

        return Response({'phone': obj.phone, 'temp_key': obj.temp_key}, status=status.HTTP_200_OK)
