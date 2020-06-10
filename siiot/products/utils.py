import cfscrape
import requests
from products.loader import load_credential


def crawl_request(product_url):
    # TODO: 크롤링 실패했을 경우 어떻게 처리할건지?
    # 1) 필수 데이터(name 등)를 먼저 주고, server 에서 detail image 크롤링 시도 + slack alert +
    # CrawlProduct 에서 성공,실패 field 저장 필요. 이를 참고하여 실패면 재요청 코드
    crawler_server = load_credential('CRAWLER_SERVER')
    body = {
        'product_url': product_url
    }
    response = requests.post(crawler_server, data=body)
    print(response)
    return response.json()['product_id']


def check_product_url(product_url):
    response = requests.post(product_url)

    # requests 로 요청
    if response.status_code == 200:
        return True

    # 403 forbidden 인 경우 cfscrape로 요청 시도
    scraper = cfscrape.create_scraper()
    r = scraper.get(product_url)
    if r.status_code == 200:
        return True
    return False
