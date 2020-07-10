from django.urls import path, include
from rest_framework.routers import SimpleRouter
from transaction.views import TransactionViewSet

router = SimpleRouter()
router.register('transaction', TransactionViewSet, basename='accounts')

urlpatterns = [
    path('', include(router.urls)),
]

