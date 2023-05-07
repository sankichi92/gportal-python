from pathlib import Path
from typing import Any, Optional

import h5py
import rasterio
import rasterio.crs
import rasterio.transform


class GCOMCFileError(Exception):
    """Raised when a GCOM-C HDF5 file is invalid."""

    pass


class GCOMCFile:
    """GCOM-C HDF5 file reader.

    Attributes:
        h5_file: [`h5py.File`][h5py.File] object.
    """

    def __init__(self, h5_file: h5py.File):
        self.h5_file: h5py.File = h5_file

    @classmethod
    def convert_to_geotiff(
        cls, input_path: str, output_dir: str = ".", target_image_data: Optional[list[str]] = None
    ) -> list[str]:
        """Converts a GCOM-C HDF5 file to GeoTIFF files.

        Args:
            input_path: Path to a GCOM-C HDF5 file.
            output_dir: Directory to save the GeoTIFF files.
            target_image_data: Image data names to convert. If not provided, all image data are converted.

        Returns:
            A list of paths to the converted GeoTIFF files.
        """
        with cls.open(input_path) as gcomc_file:
            return gcomc_file.save_as_geotiff(output_dir, target_image_data=target_image_data)

    @classmethod
    def open(cls, path: str) -> "GCOMCFile":
        """Opens a GCOM-C HDF5 file.

        Args:
            path: Path to a GCOM-C HDF5 file.

        Returns:
            An instance of [`GCOMCFile`][gportal.file.gcomc.GCOMCFile].
        """
        h5_file = h5py.File(path)

        if "Global_attributes" not in h5_file:
            raise ValueError("Not a GCOM-C file.")

        satellite = h5_file["Global_attributes"].attrs.get("Satellite")
        if not satellite or satellite[0] != b"Global Change Observation Mission - Climate (GCOM-C)":
            raise ValueError("Not a GCOM-C file.")

        return cls(h5_file)

    def close(self) -> None:
        """Closes the file."""
        self.h5_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @property
    def attrs(self) -> dict[str, Any]:
        """Global attributes."""
        return {k: v for k, v in self.h5_file["Global_attributes"].attrs.items()}

    @property
    def geometry_attrs(self) -> dict[str, Any]:
        """Geometry data attributes."""
        return {k: v for k, v in self.h5_file["Geometry_data"].attrs.items()}

    @property
    def image_data(self) -> h5py.Group:
        """Image data group."""
        image_data = self.h5_file["Image_data"]

        if not isinstance(image_data, h5py.Group):
            raise GCOMCFileError(f"Image_data is not a group: {type(image_data)}")

        return image_data

    @property
    def image_data_keys(self) -> list[str]:
        """Image data names."""
        return list(self.image_data.keys())

    def save_as_geotiff(self, output_dir: str = ".", target_image_data: Optional[list[str]] = None) -> list[str]:
        """Saves the file as GeoTIFF.

        Args:
            output_dir: Directory to save the GeoTIFF files.
            target_image_data: Image data names to save. If not provided, all image data are saved.

        Returns:
            List of paths to the saved GeoTIFF files.
        """
        if target_image_data is None:
            target_image_data = self.image_data_keys

        crs, transform = self._build_crs_and_transform()

        output_paths = []
        for image_data_name in target_image_data:
            file_name = self.attrs["Product_file_name"][0].decode()
            output_path = Path(output_dir) / f"{Path(file_name).stem}-{image_data_name}.tif"
            output_paths.append(str(output_path))

            dataset = self.image_data[image_data_name]
            if not isinstance(dataset, h5py.Dataset):
                raise GCOMCFileError(f"Image_data/{image_data_name} is not a dataset.")

            raw_error_dn = dataset.attrs["Error_DN"]
            if not isinstance(raw_error_dn, h5py.Empty):
                error_dn = raw_error_dn[0]
            else:
                error_dn = None

            with rasterio.open(
                output_path,
                mode="w",
                driver="GTiff",
                height=dataset.shape[0],
                width=dataset.shape[1],
                count=1,
                dtype=dataset.dtype,
                crs=crs,
                transform=transform,
                nodata=error_dn,
            ) as dst:
                raw_offset = dataset.attrs["Offset"]
                if not isinstance(raw_offset, h5py.Empty):
                    dst.offsets = (raw_offset[0],)

                raw_slope = dataset.attrs["Slope"]
                if not isinstance(raw_slope, h5py.Empty):
                    dst.scales = (raw_slope[0],)

                dst.write(dataset, 1)

        return output_paths

    def _build_crs_and_transform(self) -> tuple[rasterio.crs.CRS, rasterio.transform.Affine]:
        geometry_attrs = self.geometry_attrs
        projection = geometry_attrs["Image_projection"][0].decode()

        if projection == "Equal Rectangular projection":
            crs = rasterio.CRS.from_epsg(4326)
            transform = rasterio.transform.from_bounds(
                west=geometry_attrs["Lower_left_longitude"][0],
                south=geometry_attrs["Lower_left_latitude"][0],
                east=geometry_attrs["Upper_right_longitude"][0],
                north=geometry_attrs["Upper_right_latitude"][0],
                width=geometry_attrs["Number_of_pixels"][0],
                height=geometry_attrs["Number_of_lines"][0],
            )
            return crs, transform
        else:
            raise NotImplementedError(f"Projection {projection} is not supported.")
