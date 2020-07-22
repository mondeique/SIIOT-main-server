import datetime
import uuid

import cfscrape
import requests
from products.loader import load_credential
from products.slack import slack_message


def crawl_request(product_url):
    # TODO: 크롤링 실패했을 경우 어떻게 처리할건지?
    # 1) 필수 데이터(name 등)를 먼저 주고, server 에서 detail image 크롤링 시도 + slack alert +
    # CrawlProduct 에서 성공,실패 field 저장 필요. 이를 참고하여 실패면 재요청 코드
    crawler_server = load_credential('CRAWLER_SERVER')
    body = {
        'product_url': product_url
    }
    response = requests.post(crawler_server, data=body)

    # crawling 성공 (기본 정보는 저장됨. detail image 부분은 crawling server에서 처리
    if response.status_code == 201:
        return True, response.json()['product_id']

    # crawling 실패! (기본 정보도 없음. 이 경우는 임시 업로드 처리 및 임시 사진 대체)
    if response.status_code == 204:
        return False, None

    # crawling 서버 오류 (슬랙 알림 필요)
    slack_message("[크롤링 서버 에러] 크롤링 서버 에러가 발생하였습니다.\n[{}] 서버를 확인 해 주세요. \n| url: {}".
                  format(datetime.datetime.now().strftime('%y/%m/%d %H:%M'), product_url),
                  'crawling_server_error')
    return False, None


def check_product_url(product_url):
    if not product_url.startswith('http'):
        product_url = 'http://' + product_url
    print(product_url)
    response = requests.post(product_url)

    if response.status_code != 200:
        # 403 forbidden 인 경우 cfscrape로 요청 시도
        scraper = cfscrape.create_scraper()
        response = scraper.get(product_url)

    if response.status_code == 200:
        return True

    return False


def image_key_list(count):
    """
    이미지 첨부시 uuid list를 발급받는 함수입니다.
    api 가 아닌경우 utils 에서 참조하여 사용합니다.
    """
    temp_key_list = []
    for i in range(count):
        temp_key = fun_temp_key()
        temp_key_list.append(temp_key)
    return temp_key_list

def fun_temp_key():
    ext = 'jpg'
    key = uuid.uuid4()
    image_key = "%s.%s" % (key, ext)
    url = "https://{}.s3.amazonaws.com/".format('siiot-media-storage') # TODO: production s3
    content_type = "image/jpeg"
    data = {"url": url, "image_key": image_key, "content_type": content_type, "key": key}
    return data