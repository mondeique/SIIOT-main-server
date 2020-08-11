from django.urls import path, include
from rest_framework.routers import SimpleRouter
from transaction.views import TransactionViewSet, DeliveryCodeListViewSet

router = SimpleRouter()
router.register('transaction', TransactionViewSet, basename='accounts')
router.register('delivery_code', DeliveryCodeListViewSet, basename='accounts')

urlpatterns = [
    path('', include(router.urls)),
]

