import json
import re
from functools import cache
from pathlib import Path
from typing import Any, Union

from . import http_client

Datasets = dict[str, Union["Datasets", list[str]]]


def datasets() -> Datasets:
    """Fetches the dataset tree from G-Portal.

    The tree's structure corresponds to the "spacecraft/sensor" search tree of the Web UI.
    The leaves are dataset IDs.

    Note:
        This depends on an undocumented API of G-Portal, which is subject to change.
        If this function is broken, use [`cached_datasets()`][gportal.dataset.cached_datasets] instead.

    Returns:
        The dictionary of the dataset tree, where the leaves are dataset IDs.
    """
    raw_tree = http_client.get("/gpr/search/service/satsensor.json")
    return _build_datasets(raw_tree)


def _build_datasets(tree: list[dict[str, Any]], root: bool = True) -> dict[str, Any]:
    datasets = {}

    for node in tree:
        if root:
            title = re.sub(r"<img[^>]*>", "", node["title"]).rstrip()
        else:
            title = node["title"]

        children = node.get("children")
        if children:
            datasets[title] = _build_datasets(children, root=False)
        else:
            datasets[title] = node["dataset"].split(",")

    return datasets


@cache
def cached_datasets() -> Datasets:
    """Loads the dataset tree from the cache included in this package.

    Returns:
        The dictionary of the dataset tree, where the leaves are dataset IDs.
    """
    dataset_path = Path(__file__).parent / "data/datasets.json"
    with dataset_path.open() as f:
        datasets: dict[str, Any] = json.load(f)
        return datasets
