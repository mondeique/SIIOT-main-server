from django.urls import path, include
from rest_framework.routers import SimpleRouter

from notification.views import NotificationViewSet

router = SimpleRouter()
router.register('notification', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
