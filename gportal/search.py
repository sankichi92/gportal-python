from collections.abc import Iterator
from datetime import datetime
from functools import cache
from typing import Any, Optional, Union

from . import http_client
from .product import Product


def search(
    dataset_ids: list[str] = [],
    bbox: Union[list[float], tuple[float, float, float, float], None] = None,
    start_time: Union[str, datetime, None] = None,
    end_time: Union[str, datetime, None] = None,
    count: int = 100,
    params: dict[str, Any] = {},
    timeout: Optional[float] = 120,
) -> "Search":
    """Searches products on G-Portal with the given parameters.

    A search is executed by calling G-Portal CSW (Catalog Service for the Web) API.
    See G-Portal User's Manual Appendix 7 for more details of it:
    https://gportal.jaxa.jp/gpr/assets/mng_upload/COMMON/upload/GPortalUserManual_en.pdf

    Args:
        dataset_ids: List of dataset IDs.
        bbox: Bounding box of coordinates.
        start_time: Observation start time.
        end_time: Observation end time.
        count: Number of products per page.
        params: Additional search parameters. See G-Portal User's Manual.
        timeout: Timeout in seconds.

    Returns:
        A [Search][gportal.search.Search] instance that can be used to iterate through Products.
    """

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
    """Deferred query for G-Portal CSW (Catalog Service for the Web) API.

    Attributes:
        timeout: Timeout in seconds.
    """

    def __init__(
        self,
        dataset_ids: list[str] = [],
        bbox: Union[list[float], tuple[float, float, float, float], None] = None,
        start_time: Union[str, datetime, None] = None,
        end_time: Union[str, datetime, None] = None,
        count: int = 100,
        params: dict[str, Any] = {},
        timeout: Optional[float] = 120,
    ):
        self._params = params

        if dataset_ids:
            self._params["datasetId"] = ",".join(map(str, dataset_ids))

        if bbox:
            self._params["bbox"] = ",".join(map(str, bbox))

        if isinstance(start_time, datetime):
            self._params["startTime"] = start_time.isoformat()
        elif start_time:
            self._params["startTime"] = start_time

        if isinstance(end_time, datetime):
            self._params["endTime"] = end_time.isoformat()
        elif end_time:
            self._params["endTime"] = end_time

        self._params["count"] = count
        self.timeout: Optional[float] = timeout

    @cache
    def matched(self) -> int:
        """Gets the number of products matched the query.

        This method is cached, so it is safe to call it multiple times.

        Returns:
            The number of products matched the query.
        """
        page = next(self.pages())
        return page["properties"]["numberOfRecordsMatched"]

    def products(self) -> Iterator[Product]:
        """Yields products matched the query.

        Yields:
            A [Product][gportal.product.Product] instance.
        """
        for page in self.pages():
            for product_dict in page.get("features", []):
                yield Product(product_dict)

    def pages(self) -> Iterator[dict[str, Any]]:
        """Iterates a search request with pagination.

        Yields:
            A dictionary of GeoJSON FeatureCollection.
        """
        start_index = 1

        while True:
            page = http_client.get(
                "/csw/csw",
                params={
                    **self._params,
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
