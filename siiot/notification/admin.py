from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.models import Permission
from django import forms
from rest_framework.authtoken.models import Token
from accounts.nickname.models import FirstNickName, LastNickName
from custom_manage.sites import superadmin_panel, staff_panel
from custom_manage.tools import superadmin_register

from push_notifications.models import GCMDevice

from notification.models import NotificationUserLog, Notification

staff_panel.register(NotificationUserLog)
staff_panel.register(Notification)
