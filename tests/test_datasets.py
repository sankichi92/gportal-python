import responses

from gportal.datasets import ENDPOINT, datasets


@responses.activate
def test_datasets():
    # Given
    responses.get(
        ENDPOINT,
        json=[
            {
                "title": "GCOM-C/SGLI　<img src='/gpr/assets/img/icons_download.png'>",
                "children": [{"title": "L1A-Visible & Near Infrared, VNR", "dataset": "10001000"}],
            },
        ],
    )

    # When
    res = datasets()

    # Then
    assert res["GCOM-C/SGLI"]["L1A-Visible & Near Infrared, VNR"] == ["10001000"]
