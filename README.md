# gportal-python

Python CSW (Catalog Services for the Web) and SFTP client for [G-Portal](https://gportal.jaxa.jp/).

## Installation

    $ pip install gportal

## Quickstart

```python
import gportal
import os

# Get the dictionary of the G-Portal dataset, which corresponds to the spacecraft / sensor search tree of Web UI.
datasets = gportal.datasets()

# Build the search query.
res = gportal.search(
    dataset_ids=datasets["GCOM-C/SGLI"]["LEVEL2"]["Land area"]["L2-LST"],
    start_time="2023-03-25T00:00:00",
    end_time="2023-03-25T23:59:59",
    bbox=[130, 30, 140, 40],
    params={
        # Additional parameters.
        # See Appendix 7 of G-Portal User's Manual for more detail.
    },
)

print(f"Matched: {res.matched()}")

# Get a generator of Product, which represents a search result (GeoJSON).
products = res.products()

# Download the product files.
with gportal.sftp(username="sankichi92", password=os.getenv("GPORTAL_PASSWORD")) as sftp:
    sftp.download(
        remote_paths=[product.data_path for product in products],
        local_dir="path/to/download/dir",
    )
```

## Development

This project uses [Poetry](https://python-poetry.org/) as a package manager.

### Install dependencies

    $ poetry install

### Run the test suite

    $ poetry run pytest

## License

[MIT License](LICENSE)
