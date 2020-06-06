import requests
from products.loader import load_credential


def crawl_request(product_url):
    crawler_server = load_credential('CRAWLER_SERVER')
    body = {
        'product_url': product_url
    }
    response = requests.post(crawler_server, data=body)
    return response.json()['product_id']
