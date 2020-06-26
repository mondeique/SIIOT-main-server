from django.contrib import admin
from custom_manage.sites import staff_panel
from mypage.models import Accounts


class AccountsStaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'bank', 'bank_accounts', 'accounts_holder', 'created_at']


staff_panel.register(Accounts, AccountsStaffAdmin)
