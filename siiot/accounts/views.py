import uuid
import requests

from django.contrib.auth import (
    login as django_login,
    logout as django_logout
)
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

# Create your views here.
from accounts.models import User, PhoneConfirm
from accounts.serializers import LoginSerializer
from accounts.sms.utils import SMSManager


class AccountViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    serializer_class = LoginSerializer
    token_model = Token


class SignupSMSViewSet(viewsets.GenericViewSet):
    permission_classes = (AllowAny, )
    serializer_class = None

    def send_sms(self, request, *args, **kwargs):
        """
        회원가입 시 인증번호를 받는 api 입니다.
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

        if sms_manager.send_sms(phone=phone):
            return Response({'temp_key': sms_manager.temp_key}, status=status.HTTP_200_OK)

    def resend_sms(self, request, *args, **kwargs):
        pass


