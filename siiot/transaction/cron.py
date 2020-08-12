from datetime import datetime
from transaction.models import Transaction


def time_diff_in_s(start, end):
    duration_in_s = (end - start).seconds
    return duration_in_s


def check_confirm_after_deliver():
    queryset = Transaction.objects.filter(status=3)
    for transaction_obj in queryset.iterator():
        deliver_start_time = transaction_obj.deal.delivery.number_created_time
        if time_diff_in_s(deliver_start_time, datetime.now()) > (86400 * 5):
            print("AUTO TRANSACTION CONFIRM: %d".format(transaction_obj.id))

            deal = transaction_obj.deal

            transaction_obj = deal.transaction
            transaction_obj.confirm_transaction = True
            transaction_obj.status = 5
            transaction_obj.save()