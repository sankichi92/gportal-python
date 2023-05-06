from pathlib import Path
from typing import Any, Optional

import h5py
import rasterio
import rasterio.crs
import rasterio.transform


class GCOMCFile:
    """GCOM-C HDF5 file reader.

    Attributes:
        h5_file: [`h5py.File`][h5py.File] object.
    """

    def __init__(self, h5_file: h5py.File):
        self.h5_file: h5py.File = h5_file

    @classmethod
    def convert_to_geotiff(
        cls, input_path: str, output_dir: str = ".", datasets: Optional[list[str]] = None
    ) -> list[str]:
        """Converts a GCOM-C HDF5 file to GeoTIFF files.

        Args:
            input_path: Path to a GCOM-C HDF5 file.
            output_dir: Directory to save the GeoTIFF files.
            datasets: Dataset names to convert. If not provided, all datasets are converted.

        Returns:
            A list of paths to the converted GeoTIFF files.
        """
        with cls.open(input_path) as gcomc_file:
            return gcomc_file.save_as_geotiff(output_dir, datasets=datasets)

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
    def datasets(self) -> h5py.Group:
        """Dataset group."""
        return self.h5_file["Image_data"]  # type: ignore

    @property
    def dataset_names(self) -> list[str]:
        """Dataset names."""
        return list(self.datasets.keys())

    def save_as_geotiff(self, output_dir: str = ".", datasets: Optional[list[str]] = None) -> list[str]:
        """Saves the file as GeoTIFF.

        Args:
            output_dir: Directory to save the GeoTIFF files.
            datasets: Dataset names to save. If not provided, all datasets are saved.

        Returns:
            List of paths to the saved GeoTIFF files.
        """
        if datasets is None:
            datasets = self.dataset_names

        crs, transform = self._build_crs_and_transform()

        output_paths = []
        for dataset in datasets:
            file_name = self.attrs["Product_file_name"][0].decode()
            output_path = Path(output_dir) / f"{Path(file_name).stem}-{dataset}.tif"
            output_paths.append(str(output_path))

            data: h5py.Dataset = self.datasets[dataset]  # type: ignore
            with rasterio.open(
                output_path,
                mode="w",
                driver="GTiff",
                height=data.shape[0],
                width=data.shape[1],
                count=1,
                dtype=data.dtype,
                crs=crs,
                transform=transform,
                nodata=data.attrs["Error_DN"][0],  # type: ignore
            ) as dst:
                dst.offsets = (data.attrs["Offset"][0],)  # type: ignore
                dst.scales = (data.attrs["Slope"][0],)  # type: ignore
                dst.write(data, 1)

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
