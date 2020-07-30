from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.home, name='home')
]