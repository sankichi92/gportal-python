from collections.abc import Mapping
from typing import Any, Optional
from urllib.parse import urljoin

import requests

BASE_URL = "https://gportal.jaxa.jp/"


def get(path: str, params: Optional[Mapping[str, Any]] = None, timeout: Optional[float] = None) -> Any:
    url = urljoin(BASE_URL, path)
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()
