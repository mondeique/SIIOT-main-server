from django.urls import path, include
from .routers import router

app_name = 'accounts'


urlpatterns = [
    path('', include(router.urls)),
]

