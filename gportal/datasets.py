import re
from typing import Any

from . import http_client


def datasets() -> dict[str, Any]:
    """Fetches the dataset tree from G-Portal.

    The tree's structure corresponds to the "spacecraft/sensor" search tree of the Web UI.
    This depends on an undocumented API of G-Portal, which is subject to change.

    Returns:
        The dictionary of the dataset tree, where the leaves are dataset IDs.
    """

    def build_datasets(tree: list[dict[str, Any]], root: bool = True) -> dict[str, Any]:
        datasets = {}

        for node in tree:
            if root:
                title = re.sub(r"<img[^>]*>", "", node["title"]).strip()
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
