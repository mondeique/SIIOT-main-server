import string
import random
import json
from django.db.models import Sum

from accounts.nickname.models import FirstNickName, LastNickName
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


def set_random_nickname(user_model):
    adjective_list = FirstNickName.objects.values_list('id', flat=True)
    noun_list = LastNickName.objects.values_list('id', flat=True)

    # except duplicated nickname
    while True:
        first_adjective = random.choice(adjective_list)
        middle_noun = random.choice(noun_list)
        last_noun = random.choice([x for x in noun_list if x != middle_noun])

        nickname = FirstNickName.objects.get(id=first_adjective).first_nickname\
                   + LastNickName.objects.get(id=middle_noun).last_nickname\
                   + LastNickName.objects.get(id=last_noun).last_nickname
        if not user_model.objects.filter(nickname=nickname).exists() and len(nickname) <= 14:
            break

    return nickname
