from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.home, name='home'),
    path('alert_slack/', views.alert_slack),
    path('home_fit_alert_slack/', views.homefiting_alert_slack, name="homefit_alert")
]