from django.urls import path, include
from rest_framework.routers import SimpleRouter

from mypage.views import AccountsViewSet

router = SimpleRouter()
router.register('accounts', AccountsViewSet, basename='accounts')

urlpatterns = [
    path('', include(router.urls)),
]

