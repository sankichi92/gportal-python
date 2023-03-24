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
        timeout=None,
    ):
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

        if timeout is None:
            self.timeout = gportal.search_timeout
        else:
            self.timeout = timeout

    def pages(self):
        """Returns a generator of search results with automatic pagination."""

        start_index = 1

        while True:
            page = http_client.get(
                self.BASE_URL,
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
