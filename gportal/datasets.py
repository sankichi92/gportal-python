import json
import re
from functools import cache
from pathlib import Path
from typing import Any

from . import http_client


def datasets() -> dict[str, Any]:
    """Fetches the dataset tree from G-Portal.

    The tree's structure corresponds to the "spacecraft/sensor" search tree of the Web UI.

    Note:
        This depends on an undocumented API of G-Portal, which is subject to change.
        If an error raised, consider using [`cached_datasets()`](gportal.datasets.cached_datasets) instead.

    Returns:
        The dictionary of the dataset tree, where the leaves are dataset IDs.
    """

    def build_datasets(tree: list[dict[str, Any]], root: bool = True) -> dict[str, Any]:
        datasets = {}

        for node in tree:
            if root:
                title = re.sub(r"<img[^>]*>", "", node["title"]).rstrip()
            else:
                title = node["title"]

            children = node.get("children")
            if children:
                datasets[title] = build_datasets(children, root=False)
            else:
                datasets[title] = node["dataset"].split(",")

        return datasets

    raw_tree = http_client.get("/gpr/search/service/satsensor.json")
    return build_datasets(raw_tree)


@cache
def cached_datasets() -> dict[str, Any]:
    """Loads the dataset tree from the cache.

    Returns:
        The dictionary of the dataset tree, where the leaves are dataset IDs.
    """
    dataset_path = Path(__file__).parent / "data/datasets.json"
    with dataset_path.open() as f:
        datasets: dict[str, Any] = json.load(f)
        return datasets
