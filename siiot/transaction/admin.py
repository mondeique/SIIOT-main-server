from django.contrib import admin
from custom_manage.sites import staff_panel
from transaction.models import Transaction, Delivery, DeliveryCode


class TransactionStaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'status', 'seller_accepted', 'seller_cancel', 'buyer_cancel', 'confirm_transaction', 'created_at', 'canceled_at']


class DeliveryStaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'deal', 'address_info', 'state', 'code', 'number', 'number_created_time']

    def address_info(self, obj):
        return obj.address.address

class DeliveryCodeStaffAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'order', 'created_at']

staff_panel.register(Transaction, TransactionStaffAdmin)
staff_panel.register(Delivery, DeliveryStaffAdmin)
staff_panel.register(DeliveryCode, DeliveryCodeStaffAdmin)
