class Product:
    """Represents a product record in search results."""

    def __init__(self, geojson):
        self.geojson = geojson

    @property
    def geometry(self):
        return self.geojson.get("geometry")

    @property
    def properties(self):
        return self.geojson.get("properties", {})

    @property
    def id(self):
        return self.properties.get("identifier")

    @property
    def dataset_id(self):
        return self.properties.get("gpp", {}).get("datasetId")

    @property
    def start_time(self):
        return self.properties.get("beginPosition")

    @property
    def end_time(self):
        return self.properties.get("endPosition")

    @property
    def data_url(self):
        return self.properties.get("product", {}).get("fileName")

    @property
    def data_path(self):
        return self.data_url.replace("https://gportal.jaxa.jp/download/", "", 1)

    @property
    def thumbnail_url(self):
        browse = self.properties.get("browse")
        if browse is None:
            return None

        thumbnail = next((item for item in browse if item["type"] == "THUMBNAIL"), None)
        if thumbnail is None:
            return None

        return thumbnail.get("fileName")

    def flatten_properties(self):
        properties = self.properties.copy()

        if "product" in properties and isinstance(properties["product"], dict):
            for key, value in properties["product"].items():
                properties[f"product{key[0].upper()}{key[1:]}"] = value

            del properties["product"]

        if "browse" in properties and isinstance(properties["browse"], list):
            for browse in properties["browse"]:
                if "type" in browse and "fileName" in browse:
                    properties[browse["type"].lower()] = browse["fileName"]

            del properties["browse"]

        if "gpp" in properties and isinstance(properties["gpp"], dict):
            properties.update(properties["gpp"])
            del properties["gpp"]

        return properties

    def to_dict(self):
        return self.geojson

    def to_flat_properties_dict(self):
        return {
            **self.geojson,
            "properties": self.flatten_properties(),
        }
