from urllib.parse import urljoin

import requests

BASE_URL = "https://gportal.jaxa.jp/"


def get(path, params=None, timeout=None):
    url = urljoin(BASE_URL, path)
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()
