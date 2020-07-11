from django.urls import path, include
from rest_framework.routers import SimpleRouter

from chat.views import ChatRoomViewSet

router = SimpleRouter()
router.register('chat_room', ChatRoomViewSet, basename='trade')

urlpatterns = [
    path('', include(router.urls)),
]

