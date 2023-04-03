from collections.abc import Iterable, Iterator, Mapping, Sequence
from datetime import datetime
from functools import cache
from typing import Any, Optional, Union

from . import http_client
from .product import Product


def search(
    dataset_ids: Iterable[Union[str, int]] = [],
    bbox: Optional[Sequence[float]] = None,
    start_time: Union[str, datetime, None] = None,
    end_time: Union[str, datetime, None] = None,
    count: int = 100,
    params: dict[str, Any] = {},
    timeout: Optional[float] = 120,
) -> "Search":
    """Searches products on G-Portal with the given parameters.

    Note that the return value is a [`Search`][gportal.search.Search] instance.
    See its documentation for details on how to get the number of matches and iterate over results.

    Args:
        dataset_ids: List of dataset IDs.
        bbox: Bounding box of coordinates.
        start_time: Observation start time.
        end_time: Observation end time.
        count: Number of products per page.
        params: Additional search parameters. See G-Portal User's Manual.
        timeout: Timeout in seconds.

    Returns:
        A [Search][gportal.search.Search] instance that represents deferred query.
    """
    params = params.copy()

    if dataset_ids:
        params["datasetId"] = ",".join(map(str, dataset_ids))

    if bbox:
        params["bbox"] = ",".join(map(str, bbox))

    if isinstance(start_time, datetime):
        params["startTime"] = start_time.isoformat()
    elif start_time:
        params["startTime"] = start_time

    if isinstance(end_time, datetime):
        params["endTime"] = end_time.isoformat()
    elif end_time:
        params["endTime"] = end_time

    params["count"] = count

    return Search(params, timeout=timeout)


class Search:
    """Search query for G-Portal Catalogue Service API.

    For API details, see G-Portal User's Manual Appendix 7:
    https://gportal.jaxa.jp/gpr/assets/mng_upload/COMMON/upload/GPortalUserManual_en.pdf

    Attributes:
        params: Search parameters.
        timeout: Timeout in seconds.
    """

    def __init__(self, params: Mapping[str, Any], timeout: Optional[float] = None):
        self.params: Mapping[str, Any] = params
        self.timeout: Optional[float] = timeout

    def __repr__(self) -> str:
        return f"<gportal.Search params={self.params}>"

    @cache
    def matched(self) -> Optional[int]:
        """Gets the number of products matched the query.

        This method is cached, so it is safe to call it multiple times.

        Returns:
            The number of products matched the query.
        """
        response = self._request({"count": 0})
        return response.get("properties", {}).get("numberOfRecordsMatched")

    def products(self, convert_types: bool = True) -> Iterator[Product]:
        """Yields products matched the query.

        Args:
            convert_types: Whether to convert string values in properties into int, float, bool, or None.

        Yields:
            A [Product][gportal.product.Product] instance.
        """
        for page in self.pages():
            for product_dict in page.get("features", []):
                yield Product(product_dict, convert_types=convert_types)

    def pages(self) -> Iterator[dict[str, Any]]:
        """Iterates a search request with pagination.

        Yields:
            A dictionary of GeoJSON FeatureCollection.
        """
        start_index = 1

        while True:
            page = self._request({"startIndex": start_index})
            yield page

            properties = page["properties"]
            start_index += properties["numberOfRecordsReturned"]

            if start_index > properties["numberOfRecordsMatched"]:
                break

    def _request(self, extra_params: dict[str, Any]) -> dict[str, Any]:
        return http_client.get(
            "/csw/csw",
            params={
                **self.params,
                "service": "CSW",
                "version": "3.0.0",
                "request": "GetRecords",
                "outputFormat": "application/json",
                **extra_params,
            },
            timeout=self.timeout,
        )
