from django.contrib import admin
from custom_manage.sites import staff_panel
from transaction.models import Transaction, Delivery


staff_panel.register(Transaction)
staff_panel.register(Delivery)
