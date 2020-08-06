from django.db.models import F

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny

# Create your views here.
from accounts.models import User
from transaction.models import Transaction
from mypage.models import Accounts, Address
from mypage.serializers import SoldHistorySerializer, PurchasedHistorySerializer, \
    OnSaleProductSerializer, SimpleUserInfoSerializer, \
    WalletHistorySerializer, AccountsSerializer, BankListSerializer, SimpleAccountsSerializer
from payment.models import Wallet
from payment.serializers import AddressSerializer
from products.category.models import Bank
from transaction.serializers import SellerTransactionDetailSerializer, BuyerTransactionDetailSerializer


class AddressViewSet(viewsets.GenericViewSet):
    """
    주소 관련 api 입니다.
    """
    queryset = Address.objects.all()
    permission_classes = [IsAuthenticated, ]
    serializer_class = AddressSerializer

    @action(methods=['get'], detail=False)
    def recent(self, request, *args, **kwargs):
        user = request.user
        queryset = self.get_queryset().filter(user=user).order_by('-updated_at')[:3]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AccountsViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    """
    정산, 환불 계좌 생성 api 입니다.
    """
    queryset = Accounts
    permission_classes = [IsAuthenticated, ]
    serializer_class = AccountsSerializer

    def create(self, request, *args, **kwargs):
        """
        Accounts create api
        정산, 환불 계좌가 다를 수 있기 때문에 계좌는 여러개 만들 수 있습니다.
        api: POST api/v1/accounts/

        data = {'bank" :int(bank id), 'bank_accounts': str, 'accounts_holder': str}
        """
        return super(AccountsViewSet, self).create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Accounts update api
        계좌정보 업데이트 api 입니다.
        api: PUT api/v1/accounts/{id}/

        data = {'bank" :int(bank id), 'bank_accounts': str, 'accounts_holder': str}
        """
        return super(AccountsViewSet, self).update(request, *args, **kwargs)

    @action(methods=['get'], detail=False)
    def bank_list(self, request, *args, **kwargs):
        qs = Bank.objects.filter(is_active=True)
        serializer = BankListSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=False)
    def simple_accounts(self, request, *args, **kwargs):
        user = request.user
        if not user.accounts.exists():
            return Response(status=status.HTTP_204_NO_CONTENT)
        accounts = user.accounts.all().order_by('updated_at').last()
        serializer = SimpleAccountsSerializer(accounts)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StoreViewSet(viewsets.GenericViewSet):
    """
    스토어 보기 및 사용자 기본정보 조회
    """
    permission_classes = [AllowAny, ]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'profile':
            return SimpleUserInfoSerializer
        if self.action in ['sales', 'sold']:
            return OnSaleProductSerializer

    @action(methods=['get'], detail=True)
    def profile(self, request, *args, **kwargs):
        """
        사용자 기본정보 조회 api
        api: GET api/v1/store/{id}/profile/
        """
        retrieve_user = self.get_object()
        serializer = self.get_serializer(retrieve_user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['get'], detail=True)
    def sales(self, request, *args, **kwargs):
        """
        스토어 => 판매 중 + 판매완료 상품
        api: GET api/v1/store/{id}/sales/
        """
        retrieve_user = self.get_object()

        sales_products = list(retrieve_user.products.filter(status__sold=False,
                                                            temp_save=False,
                                                            is_active=True).order_by('-created_at'))
        sold_products = list(retrieve_user.products.filter(status__sold=True,
                                                           temp_save=False,
                                                           is_active=True).order_by('-created_at'))

        products = sales_products + sold_products

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class TransactionHistoryViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """
    마이페이지에서 구매내역, 판매내역, 정산내역 조회
    """
    queryset = Transaction.objects.all().select_related('deal', 'deal__seller', 'deal__buyer')\
                                        .prefetch_related('deal__trades', 'deal__trades__product',)
    permission_classes = [IsAuthenticated, ]

    def get_serializer_class(self):
        if self.action in ['sales', 'sold']:
            return SoldHistorySerializer
        elif self.action in ['purchased', 'purchase_confirmed']:
            return PurchasedHistorySerializer
        elif self.action == 'seller_detail':
            return SellerTransactionDetailSerializer
        elif self.action == 'buyer_detail':
            return BuyerTransactionDetailSerializer

    @action(methods=['get'], detail=True)
    def seller_detail(self, request, *args, **kwargs):
        """
        주문 상세조회
        api: GET api/v1/transaction-history/{id}/seller_detail/
        * id : transaction id
        """
        transaction_obj = self.get_object()
        deal = transaction_obj.deal
        user = request.user

        if not deal.seller == user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(transaction_obj)
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def buyer_detail(self, request, *args, **kwargs):
        """
        주문 상세조회
        api: GET api/v1/transaction-history/{id}/buyer_detail/
        * id : transaction id
        """
        transaction_obj = self.get_object()
        deal = transaction_obj.deal
        user = request.user

        if not deal.buyer == user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(transaction_obj)
        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def sales(self, request, *args, **kwargs):
        """
        판매내역 : 결제완료 => 승인대기, 배송중, 준비중 등의 거래 중인 상품들
        api: GET api/v1/transaction-history/sales/
        """
        user = request.user
        queryset = self.get_queryset().filter(deal__seller=user, status__in=[1,2,3,4]).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def sold(self, request, *args, **kwargs):
        """
        판매내역 :  판매확정(rename 필요), 판매완료 및 판매자 거절, 거래취소 등의 상태로 거래가 완료된 상품들
        api: GET api/v1/transaction-history/sold/
        """
        user = request.user
        queryset = self.get_queryset().filter(deal__seller=user, status__in=[5,-1,-2,-3]).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def purchased(self, request, *args, **kwargs):
        """
        구매내역 => 결제완료 : 결제완료된 상품. 즉 거래중인 상품
        api: GET api/v1/transaction-history/purchased/
        """
        user = request.user
        queryset = self.get_queryset()\
            .filter(deal__buyer=user, status__in=[1,2,3,4]).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @action(methods=['get'], detail=False)
    def purchase_confirmed(self, request, *args, **kwargs):
        """
        구매내역 => 구매확정 : 구매확정 한 상품 보여줌 + 구매취소 상품 보여줌
        api: GET api/v1/transaction-history/purchase_confirmed/
        """
        user = request.user
        queryset = self.get_queryset()\
            .filter(deal__buyer=user, status__in=[5,-1,-2,-3]).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)


class WalletViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Wallet.objects.all()
    permission_classes = [IsAuthenticated, ]
    serializer_class = WalletHistorySerializer

    def list(self, request, *args, **kwargs):
        """
        정산내역 : 계좌는 따로 요청해야함
        api: GET api/v1/wallet/
        """
        user = request.user
        queryset = self.get_queryset().filter(seller=user).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)