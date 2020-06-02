import string
import random
import json
from accounts.models import PhoneConfirm
from django.db.models import Sum
from .loader import load_credential
import requests


def generate_random_key(length=10):
    return ''.join(random.choices(string.digits+string.ascii_letters, k=length))


def create_token(token_model, user):
    token, _ = token_model.objects.get_or_create(user=user)
    return token


class Cashier:
    def __init__(self, user):
        self.user = user
        self.walletlogs = self.get_logs()
        self.sum = self.sum_logs()

    def get_logs(self):
        return WalletLog.objects.filter(user=self.user)

    def sum_logs(self):
        return self.walletlogs.aggregate(Sum('amount'))['amount__sum']

    def is_validated(self, amount):
        if self.sum_logs() + amount >= 0:
            return True
        return False

    def write_log(self):
        if self.walletlogs:
            pass

    def create_log(self, amount, log='', payment=None):
        if amount < 0:
            if self.is_validated(amount):
                raise ValueError
        newlog = WalletLog(
            user=self.user,
            amount=amount,
            log=log,
        )
        if payment:
            newlog.payment = payment
        newlog.save()
        return newlog


class JusoMaster:
    url = "http://www.juso.go.kr/addrlink/addrLinkApi.do"
    confmKey = load_credential("juso_conrifm_key")

    def search_juso(self, keyword='', currentpage=1, countperpage=10):
        res = requests.post(self.url, data={
            'confmKey': self.confmKey,
            'keyword': keyword,
            'currentPage': currentpage,
            'countPerPage': countperpage,
            'resultType': 'json'
        })
        return (res.json()['results']['common'], res.json()['results']['juso'])


def set_random_nickname():
    return 'user'+''.join(random.choices(string.digits, k=6))