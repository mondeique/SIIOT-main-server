import json
import os

from django.core.exceptions import ImproperlyConfigured


_secrets = {}
_secret_path = os.path.join(os.path.dirname(__file__), './accounts_info.json')
if os.path.exists(_secret_path):
    with open(_secret_path) as f:
        _secrets = json.loads(f.read())


class empty(object):
    pass


def load_credential(key, default=empty):
    """
    환경 변수를 불러옵니다. (1순위: os.environ, 2순위: accounts_info.json)
    """
    if key in os.environ:
        return os.environ[key]
    elif key in _secrets:
        return _secrets[key]
    elif default == empty:
        error = 'Failed to load credential for key : "{}"; '.format(key)
        error += 'call load_credential("{}", default=...) to ignore this er.'.format(key)
        raise ImproperlyConfigured(error)
    else:
        return default