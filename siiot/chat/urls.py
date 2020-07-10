from django.urls import path, include
from rest_framework.routers import SimpleRouter

from chat.views import ChatRoomViewSet
from payment.views import TradeViewSet, PaymentViewSet

router = SimpleRouter()
router.register('chat_room', ChatRoomViewSet, basename='trade')

urlpatterns = [
    path('', include(router.urls)),
]

