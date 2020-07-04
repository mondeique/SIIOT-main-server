from django.db.models import F

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from delivery.models import Transaction
from mypage.models import Accounts
from mypage.serializers import TransactionSoldHistorySerializer, TransactionPurchasedHistorySerializer, \
    TransactionSettlementHistorySerializer, OnSaleProductSerializer
from payment.models import Wallet
from products.category.models import Bank
from products.category.serializers import BankListSerializer, AccountsSerializer


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


class TransactionHistoryViewSet(viewsets.ModelViewSet):
    """
    구매, 판매 상품 조회 api
    """
    queryset = Transaction.objects.all().select_related('deal',
                                                        'deal__trades', 'deal__trades__product',
                                                        'deal__seller', 'deal__buyer')
    permission_classes = [IsAuthenticated, ]

    def get_serializer_class(self):
        if self.action == 'sold':
            return TransactionSoldHistorySerializer
        elif self.action == 'purchased':
            return TransactionPurchasedHistorySerializer
        elif self.action == 'settlement':
            return TransactionSettlementHistorySerializer
        elif self.action == 'sales':
            return OnSaleProductSerializer

    @action(methods=['get'], detail=False)
    def sold(self, request, *args, **kwargs):
        user = request.user
        queryset = self.get_queryset().filter(deal__seller=user)\
            .annotate(deal_created_at=F('deal__created_at')).order_by('-deal_created_at')

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def purchased(self, request, *args, **kwargs):
        user = request.user
        queryset = self.get_queryset().filter(deal__buyer=user) \
            .annotate(deal_created_at=F('deal__created_at')).order_by('-deal_created_at')

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def settlement(self, request, *args, **kwargs):
        user = request.user
        queryset = Wallet.objects.filter(seller=user).order_by('-created_at')

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def sales(self, request, *args, **kwargs):
        user = request.user
        queryset = user.products.all().order_by('-created_at')

        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
