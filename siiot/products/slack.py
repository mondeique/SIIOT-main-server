import json
import requests

from .loader import load_credential


def slack_message(message, type):
    if type == 'upload_request':
        incomming_url = load_credential("SLACK_INCOMMING_URL", "")
    elif type == 'shopping_mall_demand':
        incomming_url = load_credential("SLACK_SHOPPINGMALL_DEMAND_INCOMMING_URL", "")
    else:
        return None
    post_data = {"text": '{}'.format(message)}
    data = json.dumps(post_data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    requests.post(incomming_url, headers=headers, data=data)
    return None
