import responses

from gportal import Search


class TestSearch:
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
            Search.BASE_URL,
            match=[responses.matchers.query_param_matcher({"startIndex": 1}, strict_match=False)],
            json=response_json,
        )
        responses.get(
            Search.BASE_URL,
            match=[responses.matchers.query_param_matcher({"startIndex": 101}, strict_match=False)],
            json=response_json,
        )

        # When
        search = Search()
        pages = search.pages()

        # Then
        assert next(pages) == response_json
        assert next(pages) == response_json
        assert next(pages, None) is None
