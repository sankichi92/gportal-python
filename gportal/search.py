import gportal

from . import http_client


class Search:
    """Represents a deferred query for G-Portal search."""

    BASE_URL = "https://gportal.jaxa.jp/csw/csw"

    def __init__(
        self,
        *,
        dataset_ids=[],
        bbox=None,
        start_time=None,
        end_time=None,
        count=100,
        params={},
    ):
        self._params = params

        if dataset_ids:
            self._params["datasetId"] = ",".join(map(str, dataset_ids))

        if bbox:
            self._params["bbox"] = ",".join(map(str, bbox))

        if start_time:
            self._params["startTime"] = start_time

        if end_time:
            self._params["endTime"] = end_time

        self._params["count"] = count

    def pages(self):
        """Returns a generator of search results with automatic pagination."""

        start_index = 1

        while True:
            page = http_client.get(
                self.BASE_URL,
                params={
                    **self._params,
                    "service": "CSW",
                    "version": "3.0.0",
                    "request": "GetRecords",
                    "outputFormat": "application/json",
                    "startIndex": start_index,
                },
                timeout=gportal.search_timeout,
            )
            yield page

            properties = page["properties"]
            start_index += properties["numberOfRecordsReturned"]

            if start_index > properties["numberOfRecordsMatched"]:
                break
