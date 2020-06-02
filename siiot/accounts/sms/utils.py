import string
import random
import json
from accounts.models import PhoneConfirm
from accounts.sms.signature import time_stamp, make_signature
from ..loader import load_credential
import requests
import uuid


class SMSManager():
    """
    인증번호 발송(ncloud 사용)을 위한 class 입니다.
    v2 로 업데이트 하였습니다. 2020.06
    """
    serviceId = load_credential("serviceId")
    access_key = load_credential("access_key")
    _from = load_credential("_from")  # 발신번호
    url = "https://sens.apigw.ntruss.com/sms/v2/services/{}/messages".format(serviceId)
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'x-ncp-apigw-timestamp': time_stamp(),
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': make_signature(),
    }

    def __init__(self):
        self.certification_number = ""
        self.temp_key = uuid.uuid4()
        self.body = {
            "type": "SMS",
            "contentType": "COMM",
            "from": self._from,
            "content": "",  # 기본 메시지 내용
            "messages": [{"to": ""}],
        }

    def create_instance(self, phone, kind):
        phone_confirm = PhoneConfirm.objects.create(
            phone=phone,
            certification_number=self.certification_number,
            temp_key=self.temp_key,
            kinds=kind
        )
        return phone_confirm

    def generate_random_key(self):
        return ''.join(random.choices(string.digits, k=4))

    def set_certification_number(self):
        self.certification_number = self.generate_random_key()

    def set_content(self):
        self.set_certification_number()
        self.body['content'] = "사용자의 인증 코드는 [SiiOt] {}입니다.".format(self.certification_number)

    def send_sms(self, phone):
        self.body['messages'][0]['to'] = phone
        request = requests.post(self.url, headers=self.headers, data=json.dumps(self.body))
        if request.status_code == 202:
            return True
        else:
            return False
