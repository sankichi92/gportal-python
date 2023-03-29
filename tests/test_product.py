import pytest

from gportal.product import Product


class TestProduct:
    @pytest.fixture
    def product(self):
        return Product(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[-180, 90], [180, 90], [180, -90], [-180, -90], [-180, 90]]],
                },
                "properties": {
                    "identifier": "GRANULE_ID",
                    "beginPosition": "2023-03-25T00:00:00Z",
                    "endPosition": "2023-03-25T23:59:50Z",
                    "product": {
                        "fileName": "https://gportal.jaxa.jp/download/path/to/GRANULE_ID.h5",
                    },
                    "browse": [
                        {
                            "type": "QUICKLOOK",
                            "fileName": "https://gportal.jaxa.jp/gpr/img/br/GRANULE_ID.png",
                        }
                    ],
                    "gpp": {
                        "datasetId": "12345678",
                    },
                },
            }
        )

    def test_geometry(self, product):
        assert product.geometry == {
            "type": "Polygon",
            "coordinates": [[[-180, 90], [180, 90], [180, -90], [-180, -90], [-180, 90]]],
        }

    def test_id(self, product):
        assert product.id == "GRANULE_ID"

    def test_dataset_id(self, product):
        assert product.dataset_id == "12345678"

    def test_start_time(self, product):
        assert product.start_time.isoformat() == "2023-03-25T00:00:00+00:00"

    def test_end_time(self, product):
        assert product.end_time.isoformat() == "2023-03-25T23:59:50+00:00"

    def test_data_url(self, product):
        assert product.data_url == "https://gportal.jaxa.jp/download/path/to/GRANULE_ID.h5"

    def test_data_path(self, product):
        assert product.data_path == "path/to/GRANULE_ID.h5"

    def test_get_browse_url(self, product):
        assert product.get_browse_url() == "https://gportal.jaxa.jp/gpr/img/br/GRANULE_ID.png"

    def test_flatten_properties(self, product):
        flat_properties = product.flatten_properties()

        assert flat_properties == {
            "identifier": "GRANULE_ID",
            "beginPosition": "2023-03-25T00:00:00Z",
            "endPosition": "2023-03-25T23:59:50Z",
            "productFileName": "https://gportal.jaxa.jp/download/path/to/GRANULE_ID.h5",
            "browse-br": "https://gportal.jaxa.jp/gpr/img/br/GRANULE_ID.png",
            "datasetId": "12345678",
        }
