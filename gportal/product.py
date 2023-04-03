import sys
from datetime import datetime
from typing import Any, Optional


class Product:
    """Wrapper of a product GeoJSON in search results.

    You can access the `properties` or `properties.gpp` values by `[]` operator like a dictionary.
    """

    VALUE_CONVERSION_MAP = {
        "": None,
        "true": True,
        "false": False,
    }

    def __init__(self, geojson: dict[str, Any], convert_types: bool = False):
        if convert_types and "properties" in geojson:
            geojson = {**geojson, "properties": self._convert_type(geojson["properties"])}

        self._geojson = geojson

    @classmethod
    def _convert_type(cls, val: Any) -> Any:
        if isinstance(val, str):
            if val in cls.VALUE_CONVERSION_MAP:
                return cls.VALUE_CONVERSION_MAP[val]
            try:
                return int(val)
            except ValueError:
                pass
            try:
                return float(val)
            except ValueError:
                pass
        elif isinstance(val, dict):
            return {key: cls._convert_type(val) for key, val in val.items()}

        return val

    def __repr__(self) -> str:
        if self.id is None:
            return super().__repr__()
        else:
            return f"<gportal.Product id={self.id}>"

    @property
    def __geo_interface__(self) -> dict[str, Any]:
        return self._geojson

    @property
    def geometry(self) -> dict[str, Any]:
        """GeoJSON geometry."""
        return self._geojson.get("geometry", {})

    @property
    def properties(self) -> dict[str, Any]:
        """GeoJSON properties."""
        return self._geojson.get("properties", {})

    def __getitem__(self, key: str) -> Any:
        if key in self.properties:
            return self.properties[key]

        if key in self.properties.get("gpp", {}):
            return self.properties["gpp"][key]

        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    @property
    def id(self) -> Optional[str]:
        """Granule ID."""
        return self.get("identifier")

    @property
    def data_url(self) -> Optional[str]:
        """URL of the product file."""
        return self.get("product", {}).get("fileName")

    @property
    def data_path(self) -> Optional[str]:
        """Path to the product file on the SFTP server."""
        if self.data_url is None:
            return None

        return self.data_url.replace("https://gportal.jaxa.jp/download/", "", 1)

    @property
    def quicklook_url(self) -> Optional[str]:
        """Quicklook image URL."""
        for item in self.get("browse", []):
            if item.get("type", "").lower() == "quicklook":
                return item.get("fileName")

        return None

    def get_as_datetime(self, key: str) -> Optional[datetime]:
        """Gets a value as a datetime object."""
        val = self.get(key)
        if val is None:
            return None

        if sys.version_info < (3, 11):
            val = val.replace("Z", "+00:00")

        return datetime.fromisoformat(val)

    def flatten_properties(self) -> dict[str, Any]:
        """Flattens the nested properties.

        This method processes nested properties from the following keys:

        - `product`: Each key is prefixed with `product` (e.g. `product.fileName` => `productFileName`).
        - `browse`: Keys are the `type` fields (e.g. quicklook, thumbnail), and their values are `fileName` fields.
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
            for i, browse in enumerate(properties["browse"]):
                if "type" in browse and "fileName" in browse:
                    type = browse["type"].lower()
                    if type in properties:
                        properties[f"{type}{i}"] = browse["fileName"]
                    else:
                        properties[type] = browse["fileName"]

            del properties["browse"]

        if "gpp" in properties and isinstance(properties["gpp"], dict):
            properties.update(properties["gpp"])
            del properties["gpp"]

        return properties

    def to_dict(self, flatten_properties: bool = False) -> dict[str, Any]:
        """Converts to a dictionary of GeoJSON Feature.

        Args:
            flatten_properties: If True, the properties are flattened using
                [`flatten_properties`][gportal.product.Product.flatten_properties].

        Returns:
            This product as a dictionary.
        """
        if flatten_properties:
            return {
                **self._geojson,
                "properties": self.flatten_properties(),
            }
        else:
            return self._geojson
