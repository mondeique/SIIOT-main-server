from django.urls import path, include
from rest_framework.routers import SimpleRouter
from payment.views import TradeViewSet, PaymentViewSet

router = SimpleRouter()
router.register('trade', TradeViewSet, basename='trade')
router.register('payment', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]

