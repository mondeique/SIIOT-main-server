from custom_manage.sites import staff_panel
from django.contrib import admin
from user_activity.models import RecentlySearchedKeyword


class RecentlySearchedKeywordStaffAdmin(admin.ModelAdmin):
    fields = ('user', 'keyword', 'recent', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


staff_panel.register(RecentlySearchedKeyword, RecentlySearchedKeywordStaffAdmin)

