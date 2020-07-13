from django.contrib import admin
from custom_manage.sites import staff_panel
from notice.models import Notice


class NoticeStaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'hidden', 'created_at', 'updated_at']


staff_panel.register(Notice, NoticeStaffAdmin)
