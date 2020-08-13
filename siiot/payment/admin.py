from custom_manage.sites import staff_panel
from payment.models import Commission, Wallet, Trade, Deal, Payment, PaymentErrorLog, TradeErrorLog
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


class CommissionAdmin(admin.ModelAdmin):
    list_display = ['pk','rate','created_at','updated_at']
    list_editable = ('rate',)


class TradeAdmin(admin.ModelAdmin):
    list_display = ['pk', 'product', 'deal', 'status', 'created_at', 'updated_at']
    list_filter = ('status',)


class DealAdmin(admin.ModelAdmin):
    list_display = ['pk', 'buyer', 'seller', 'trade', 'product', 'pay_product', "transaction_info", 'transaction_completed_date',
                    'total', 'remain', 'status', 'is_settled']
    list_filter = ['status', 'is_settled']

    def trade(self, obj):
        if obj.trades.exists():
            return obj.trades.first()
        return None

    def pay_product(self, obj):
        payment = obj.payment
        return payment.name

    def product(self, obj):
        if obj.trades.exists():
            return obj.trades.first().product
        return None

    def transaction_info(self, obj):
        if hasattr(obj, 'transaction'):
            return obj.transaction
        return None


class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id','name','user', 'receipt_id', 'status','price','requested_at','purchased_at', 'revoked_at']
    list_filter = ('status','requested_at')

#
# class WalletLogAdmin(admin.ModelAdmin):
#     list_display = ['id','user', 'user_bank_info', 'deal_remain', 'status','created_at','updated_at', 'is_settled']
#     list_filter = ['status', 'created_at']
#     list_editable = ['is_settled']
#
#     def user_bank_info(self, obj):
#         store_account = obj.deal.seller.account
#         bank = store_account.get_bank_display()
#         account = store_account.account
#         holder = store_account.account_holder
#         return '[예금주: {}] {}, {}'.format(holder, bank, account)
    #
    # def deal_link(self, obj):
    #     if obj.deal:
    #         return mark_safe('<a href={}>{}</a>'.format(
    #             reverse("admin:payment_deal_change", args=(obj.deal.pk,)),
    #             obj.deal
    #         ))
    #     return '-'

    # def deal_remain(self, obj):
    #     if obj.deal:
    #         return '{} 원'.format(obj.deal.remain)
    #
    # deal_remain.short_description = "남은 정산액"
    # user_bank_info.short_description = "판매자 계좌정보"


class DeliveryMemoAdmin(admin.ModelAdmin):
    list_display = ['id', 'memo', 'is_active', 'order']
    list_editable = ['order']


staff_panel.register(Commission, CommissionAdmin)
staff_panel.register(Trade, TradeAdmin)
staff_panel.register(Deal, DealAdmin)
staff_panel.register(Payment, PaymentAdmin)
# staff_panel.register(Wallet, WalletLogAdmin)
staff_panel.register(PaymentErrorLog)
staff_panel.register(TradeErrorLog)

