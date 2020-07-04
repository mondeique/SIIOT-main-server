from django.urls import path, include
from rest_framework.routers import SimpleRouter

from mypage.views import AccountsViewSet, TransactionHistoryViewSet

router = SimpleRouter()
router.register('accounts', AccountsViewSet, basename='accounts')
router.register('transaction', TransactionHistoryViewSet, basename='accounts')

urlpatterns = [
    path('', include(router.urls)),
]

