import uuid

from django.db import transaction
from django.db.models import Case, When, IntegerField, Count
from django.http import Http404
from django.utils import timezone

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.
from mypage.models import Accounts
from products.category.models import FirstCategory, SecondCategory, Size, Color, Bank
from products.category.serializers import FirstCategorySerializer, SecondCategorySerializer, SizeSerializer, \
    ColorSerializer, BankListSerializer, AccountsSerializer


class AccountsViewSet(viewsets.ModelViewSet):
    queryset = Accounts
    permission_classes = [IsAuthenticated, ]
    serializer_class = AccountsSerializer

    def create(self, request, *args, **kwargs):
        """
        Accounts create api
        api: POST api/v1/accounts/

        data = {'bank" :int(bank id), 'bank_accounts': str, 'accounts_holder': str}
        """
        user = request.user
        if hasattr(user, 'accounts'):
            serializer = self.get_serializer(user.accounts, data=request.data)
        else:
            serializer = self.get_serializer(request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=False)
    def bank_list(self, request, *args, **kwargs):
        qs = Bank.objects.filter(is_active=True)
        serializer = BankListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
