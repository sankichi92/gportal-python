import re

from . import http_client

ENDPOINT = "https://gportal.jaxa.jp/gpr/search/service/satsensor.json"


def datasets():
    """Gets and builds the dictionary of the dataset tree, where the leaves are the dataset IDs."""

    def build_datasets(tree, root=True):
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

    raw_tree = http_client.get(ENDPOINT)
    return build_datasets(raw_tree)
