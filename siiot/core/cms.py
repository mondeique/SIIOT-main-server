# -*- encoding: utf-8 -*-
import requests
from django.conf import settings
from django.core.cache import cache

"""
config management server ( jarvis ) 를 통해서 url 을 가져올때 사용되는 util
"""

CMS_PROD_URL = 'http://jarvis-production.pfeg2r4ezj.ap-northeast-2.elasticbeanstalk.com/'
CMS_DEV_URL = 'http://222.110.255.105:7878/'


class CMS(object):
    CHAT_SERVER_DOMAIN = 'chat_server_domain'
    CHAT_PROXY_SERVER_DOMAIN = 'chat_proxy_server_domain'

    LABEL_SERVER_ENDPOINT = 'label_server_endpoint'

    CMS_CONFIG = 'config'

    def __init__(self, request=None, cms_url=CMS_PROD_URL):
        """
        사용자로부터 전달받은 request 가 있을때는 해당 request 의 header 의 정보를 이용해서 config_name, locale 정보를 가져온다.
        request 가 없을 경우에는 environment 에 등록되어 있는 X-Jarvis-Config 에 등록된 값을 이용해서 정보를 가져온다.
        :param request:
        :param cms_url:
        """
        self.cms_url = cms_url

        if request and request.META:
            self.locale = request.service_locale

            config_name = request.META.get('HTTP_X_JARVIS_CONFIG', None)
            if config_name:
                self.config_name = config_name
            else:
                self.config_name = settings.JARVIS_CONFIG
        else:
            self.config_name = settings.JARVIS_CONFIG
            self.locale = settings.SERVICE_LOCALE

        requests_session = requests.Session()
        requests_adapters = requests.adapters.HTTPAdapter(max_retries=3)
        requests_session.mount('https://', requests_adapters)
        self.requests_session = requests_session

    class ResponseError(Exception):
        def __init__(self, message=None):
            self.message = message

    @staticmethod
    def get_response(response):
        if response.status_code != requests.codes.ok:
            result = response.json()
            raise CMS.ResponseError(result.get('Error'))
        result = response.json()
        return result

    def _get(self, url, payload=None):
        response = self.requests_session.get(url, params=payload)
        return self.get_response(response)

    def get_config(self):
        url = '{}configs/{}?locale={}'.format(self.cms_url, self.config_name, self.locale)
        result = self._get(url)
        return result.get(self.CMS_CONFIG)

    def get_key_name_config(self, key_name):
        if self.config_name == 'prod':
            # prod 에 대한 키들은 한번 cacheing 처리를 하여서 자주 api call 을 하지 않도록 한다.
            cache_key = "CMS_" + self.config_name + "_" + key_name + '_' + self.locale
            config_value = cache.get(cache_key, None)
        else:
            cache_key = None
            config_value = None

        if config_value is None:
            url = '{url}configs/{name}/{key}?locale={locale}'.format(
                url=self.cms_url,
                name=self.config_name,
                key=key_name,
                locale=self.locale
            )

            result = self._get(url)
            config_value = result.get(key_name, None)
            if config_value:
                if cache_key:
                    cache.set(cache_key, config_value, 60)
                return config_value
            else:
                raise CMS.ResponseError('key error')
        else:
            return config_value
