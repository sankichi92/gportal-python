# gportal-python

Unofficial python client for [G-Portal](https://gportal.jaxa.jp/) Catalogue Service and SFTP.

This package is distributed under the [MIT License](https://mit-license.org/), but the data that can be retrieved through this package is provided under [G-Portal Terms of Use](https://gportal.jaxa.jp/gpr/index/eula).
Please make sure to review them before using the G-Portal data.

## Installation

    $ pip install gportal

## Quickstart

```python
import gportal

# Get the dictionary of the G-Portal dataset.
# It corresponds to the "spacecraft/sensor" search tree of the Web UI.
datasets = gportal.datasets()

# Build a search query.
res = gportal.search(
    dataset_ids=datasets["GCOM-C/SGLI"]["LEVEL2"]["Land area"]["L2-LST"],
    start_time="2023-03-25T00:00:00",
    end_time="2023-03-25T23:59:59",
    bbox=[130, 30, 140, 40],
    params={
        # You can add more parameters.
        # See Appendix 7 of G-Portal User's Manual for more details:
        # https://gportal.jaxa.jp/gpr/assets/mng_upload/COMMON/upload/GPortalUserManual_en.pdf
    },
)

print("Matched:", res.matched())

# Get the resulting products.
products = res.products()

# Download the product files via SFTP.
gportal.username = "sankichi92"  
gportal.password = "**********"  # If env var GPORTAL_PASSWORD is set, the value is used.
gportal.download(products, local_dir="path/to/download/dir")
```

## Documentation

https://gportal.readthedocs.io/

## Development

This project uses [Poetry](https://python-poetry.org/).

### Install dependencies

    $ poetry install

### Run the test suite

    $ poetry run pytest

### Start the docs server

    $ poetry run mkdocs serve

### Release a new version

1. Bump the version in `pyproject.toml` by [`poetry version`](https://python-poetry.org/docs/cli/#version) and commit it.
2. Create a git tag for the new version.
3. Push it to GitHub, and then the `publish-package` workflow starts.
