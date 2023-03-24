from .search import Search

search_timeout = 120


def search(dataset_ids=[], bbox=None, start_time=None, end_time=None, count=100, params={}, timeout=None):
    """Search products with the given parameters."""

    return Search(
        dataset_ids=dataset_ids,
        bbox=bbox,
        start_time=start_time,
        end_time=end_time,
        count=count,
        params=params,
        timeout=timeout,
    )
