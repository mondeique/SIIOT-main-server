from django.urls import path, include

from accounts.views import search_address_page
from .routers import router

app_name = 'accounts'


urlpatterns = [
    path('', include(router.urls)),
    path('search_address/', search_address_page),
]

