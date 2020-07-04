from django.contrib import admin
from custom_manage.sites import staff_panel
from delivery.models import Transaction, Delivery


staff_panel.register(Transaction)
staff_panel.register(Delivery)
