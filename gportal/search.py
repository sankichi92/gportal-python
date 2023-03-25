from functools import lru_cache

from . import http_client
from .product import Product


def search(dataset_ids=[], bbox=None, start_time=None, end_time=None, count=100, params={}, timeout=120):
    """Searches products with the given parameters."""

    return Search(
        dataset_ids=dataset_ids,
        bbox=bbox,
        start_time=start_time,
        end_time=end_time,
        count=count,
        params=params,
        timeout=timeout,
    )


class Search:
    """Represents a deferred query for G-Portal search."""

    def __init__(self, dataset_ids=[], bbox=None, start_time=None, end_time=None, count=100, params={}, timeout=120):
        self.params = params

        if dataset_ids:
            self.params["datasetId"] = ",".join(map(str, dataset_ids))

        if bbox:
            self.params["bbox"] = ",".join(map(str, bbox))

        if start_time:
            self.params["startTime"] = start_time

        if end_time:
            self.params["endTime"] = end_time

        self.params["count"] = count
        self.timeout = timeout

    @lru_cache(maxsize=1)
    def matched(self):
        """Returns the number of search results."""

        page = next(self.pages())
        return page["properties"]["numberOfRecordsMatched"]

    def products(self):
        """Returns a generator of products."""

        for page in self.pages():
            for product_dict in page.get("features", []):
                yield Product(product_dict)

    def pages(self):
        """Returns a generator of search results with automatic pagination."""

        start_index = 1

        while True:
            page = http_client.get(
                "/csw/csw",
                params={
                    **self.params,
                    "service": "CSW",
                    "version": "3.0.0",
                    "request": "GetRecords",
                    "outputFormat": "application/json",
                    "startIndex": start_index,
                },
                timeout=self.timeout,
            )
            yield page

            properties = page["properties"]
            start_index += properties["numberOfRecordsReturned"]

            if start_index > properties["numberOfRecordsMatched"]:
                break
