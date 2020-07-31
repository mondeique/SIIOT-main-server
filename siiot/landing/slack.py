import json
import requests


def slack_message(message):
    incoming_url = 'https://hooks.slack.com/services/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'
    post_data = {"text": '{}'.format(message)}
    data = json.dumps(post_data)
    headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'}
    requests.post(incoming_url, headers=headers, data=data)
    return None