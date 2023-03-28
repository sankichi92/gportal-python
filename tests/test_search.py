from datetime import datetime

import responses

from gportal.search import Search, search


def test_search():
    # When
    res = search(
        dataset_ids=["1", "2"],
        start_time=datetime(2023, 3, 28, 0, 0, 0),
        end_time=datetime(2023, 3, 28, 23, 59, 59),
        bbox=[130, 30, 140, 40],
    )

    # Then
    assert res.params["datasetId"] == "1,2"
    assert res.params["startTime"] == "2023-03-28T00:00:00"
    assert res.params["endTime"] == "2023-03-28T23:59:59"
    assert res.params["bbox"] == "130,30,140,40"


class TestSearch:
    @responses.activate
    def test_matched(self):
        # Given
        responses.get(
            "https://gportal.jaxa.jp/csw/csw",
            json={
                "properties": {
                    "numberOfRecordsMatched": 150,
                    "numberOfRecordsReturned": 100,
                }
            },
        )

        # When
        res = Search(params={})
        matched = res.matched()

        # Then
        assert matched == 150

    @responses.activate
    def test_products(self):
        # Given
        responses.get(
            "https://gportal.jaxa.jp/csw/csw",
            match=[responses.matchers.query_param_matcher({"startIndex": 1}, strict_match=False)],
            json={
                "properties": {"numberOfRecordsMatched": 4, "numberOfRecordsReturned": 2},
                "features": [{}, {}],
            },
        )
        responses.get(
            "https://gportal.jaxa.jp/csw/csw",
            match=[responses.matchers.query_param_matcher({"startIndex": 3}, strict_match=False)],
            json={
                "properties": {"numberOfRecordsMatched": 4, "numberOfRecordsReturned": 2},
                "features": [{}, {}],
            },
        )

        # When
        res = Search(params={})
        products = res.products()

        # Then
        assert len(list(products)) == 4

    @responses.activate
    def test_pages(self):
        # Given
        response_json = {
            "properties": {
                "numberOfRecordsMatched": 200,
                "numberOfRecordsReturned": 100,
            }
        }
        responses.get(
            "https://gportal.jaxa.jp/csw/csw",
            match=[responses.matchers.query_param_matcher({"startIndex": 1}, strict_match=False)],
            json=response_json,
        )
        responses.get(
            "https://gportal.jaxa.jp/csw/csw",
            match=[responses.matchers.query_param_matcher({"startIndex": 101}, strict_match=False)],
            json=response_json,
        )

        # When
        res = Search(params={})
        pages = res.pages()

        # Then
        assert next(pages) == response_json
        assert next(pages) == response_json
        assert next(pages, None) is None
