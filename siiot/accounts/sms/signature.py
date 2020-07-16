import json

import hashlib
import hmac
import base64
import time

import requests

from ..loader import load_credential


def time_stamp():
    return str(int(time.time() * 1000))


def make_signature(string_to_sign):
    secret_key = bytes(load_credential('secret_key'), 'UTF-8')
    string = bytes(string_to_sign, 'UTF-8')
    string_hmac = hmac.new(secret_key, string, digestmod=hashlib.sha256).digest()
    string_base64 = base64.b64encode(string_hmac).decode('UTF-8')
    return string_base64


def simple_send(certification_number, phone):
    """
    simple sms send code
    """
    access_key = load_credential("access_key")
    url = "https://sens.apigw.ntruss.com"
    uri = "/sms/v2/services/" + load_credential("serviceId") + "/messages"
    api_url = url + uri
    timestamp = str(int(time.time() * 1000))
    string_to_sign = "POST " + uri + "\n" + timestamp + "\n" + access_key
    signature = make_signature(string_to_sign)

    message = "사용자의 인증 코드는 [SiiOt] {}입니다.".format(certification_number)

    headers = {
        'Content-Type': "application/json; charset=UTF-8",
        'x-ncp-apigw-timestamp': timestamp,
        'x-ncp-iam-access-key': access_key,
        'x-ncp-apigw-signature-v2': signature
    }

    body = {
        "type": "SMS",
        "contentType": "COMM",
        "from": load_credential("_from"),
        "content": message,
        "messages": [{"to": '{}'.format(phone)}]
    }

    body = json.dumps(body)

    response = requests.post(api_url, headers=headers, data=body)
    print(response.status_code)
    if response.status_code == 202:
        return True
    else:
        return False
