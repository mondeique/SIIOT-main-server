from django.urls import path, include
from rest_framework.routers import SimpleRouter
from notice.views import NoticeViewSet

router = SimpleRouter()
router.register('notice', NoticeViewSet, basename='notice')

urlpatterns = [
    path('', include(router.urls)),
]

