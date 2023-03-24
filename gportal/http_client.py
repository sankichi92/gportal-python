import requests


def get(url, params=None, timeout=None):
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()
