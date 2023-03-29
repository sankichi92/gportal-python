import re
from datetime import datetime
from typing import Any, Optional


class Product:
    """Wrapper of a product GeoJSON in search results.

    Attributes:
        geojson: Original dictionary that represents GeoJSON Feature.
    """

    def __init__(self, geojson: dict[str, Any]):
        self.geojson: dict[str, Any] = geojson

    def __repr__(self) -> str:
        if self.id is None:
            return super().__repr__()
        else:
            return f"<gportal.Product id={self.id}>"

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        return self.geojson

    @property
    def geometry(self) -> dict[str, Any]:
        """GeoJSON geometry."""
        return self.geojson.get("geometry", {})

    @property
    def properties(self) -> dict[str, Any]:
        """GeoJSON properties."""
        return self.geojson.get("properties", {})

    @property
    def id(self) -> Optional[str]:
        """Granule ID."""
        return self.properties.get("identifier")

    @property
    def dataset_id(self) -> Optional[str]:
        """Dataset ID belonging to."""
        return self.properties.get("gpp", {}).get("datasetId")

    @property
    def start_time(self) -> datetime:
        """Observation start time."""
        isoformat = re.sub(r"Z$", "+00:00", self.properties["beginPosition"])  # For Python 3.10 or former
        return datetime.fromisoformat(isoformat)

    @property
    def end_time(self) -> datetime:
        """Observation end time."""
        isoformat = re.sub(r"Z$", "+00:00", self.properties["endPosition"])  # For Python 3.10 or former
        return datetime.fromisoformat(isoformat)

    @property
    def data_url(self) -> Optional[str]:
        """URL of the product file."""
        return self.properties.get("product", {}).get("fileName")

    @property
    def data_path(self) -> Optional[str]:
        """Path to the product file on the SFTP server."""
        if self.data_url is None:
            return None

        return self.data_url.replace("https://gportal.jaxa.jp/download/", "", 1)

    def get_browse_url(self, type: str = "browse") -> Optional[str]:
        """URL of the browse image.

        Args:
            type: Type of the image. Basically, "browse", "sub-browse" or "thumbnail".
        """
        items = self.properties.get("browse")
        if items is None:
            return None

        type = {
            "thumbnail": "thm",
            "browse": "br",
            "sub-browse": "sb",
        }.get(type, type)

        for item in items:
            if f"/img/{type}" in item["fileName"]:
                return item["fileName"]

        return None

    def flatten_properties(self) -> dict[str, Any]:
        """Flattens the nested properties.

        This method processes nested properties from the following keys:

        - `product`: Each key is prefixed with `product` (e.g. `product.fileName` => `productFileName`).
        - `browse`: Keys are the image type (e.g. browse-br, browse-thm), and their values are `fileName`.
        - `gpp`: Keys and values are directly merged.

        Returns:
            The flattened properties.
        """
        properties = self.properties.copy()

        if "product" in properties and isinstance(properties["product"], dict):
            for key, value in properties["product"].items():
                properties[f"product{key[0].upper()}{key[1:]}"] = value

            del properties["product"]

        if "browse" in properties and isinstance(properties["browse"], list):
            for browse in properties["browse"]:
                match = re.search(r"\/img\/([\w]+)\/", browse.get("fileName", ""))
                if match:
                    properties[f"browse-{match.group(1)}"] = browse["fileName"]

            del properties["browse"]

        if "gpp" in properties and isinstance(properties["gpp"], dict):
            properties.update(properties["gpp"])
            del properties["gpp"]

        return properties

    def to_dict(self) -> dict[str, Any]:
        return self.geojson

    def to_flat_properties_dict(self) -> dict[str, Any]:
        """Converts to a dictionary of GeoJSON Feature with flattened properties.

        Returns:
            A dictionary of GeoJSON Feature with flattened properties.
        """
        return {
            **self.geojson,
            "properties": self.flatten_properties(),
        }
