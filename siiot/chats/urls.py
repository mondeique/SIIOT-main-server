from django.conf.urls import url, include
from django.urls import path
from rest_framework.routers import SimpleRouter

# from chats.views import ChatRoomViewSet
from chats import views
from chats.views import TestChatRoomList, TestAuth, MessageModelViewSet

router = SimpleRouter()
router.register('', TestAuth, basename='testauth')
router.register(r'message', MessageModelViewSet, basename='message-api')


urlpatterns = [
    path('', TestChatRoomList.as_view(), name='chat'),
    path('', include(router.urls)),
    path(r'api/v1/', include(router.urls)),
    url(r'^(?P<room_name>[^/]+)/$', views.room, name='room'),
]
