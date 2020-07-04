from django.contrib import admin
from custom_manage.sites import staff_panel
from mypage.models import Accounts, DeliveryPolicy


class AccountsStaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'bank', 'bank_accounts', 'accounts_holder', 'created_at']


class DeliveryPolicyStaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'general', 'mountain']


staff_panel.register(Accounts, AccountsStaffAdmin)
staff_panel.register(DeliveryPolicy, DeliveryPolicyStaffAdmin)
