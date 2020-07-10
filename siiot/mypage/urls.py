from django.urls import path, include
from rest_framework.routers import SimpleRouter

from mypage.views import AccountsViewSet, TransactionHistoryViewSet, StoreViewSet, AddressViewSet, WalletViewSet

router = SimpleRouter()
router.register('accounts', AccountsViewSet, basename='accounts')
router.register('transaction-history', TransactionHistoryViewSet, basename='accounts')
router.register('wallet', WalletViewSet, basename='accounts')
router.register('store', StoreViewSet, basename='accounts')
router.register('address', AddressViewSet, basename='accounts')

urlpatterns = [
    path('', include(router.urls)),
]

