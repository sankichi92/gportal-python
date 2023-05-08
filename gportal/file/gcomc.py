from pathlib import Path
from typing import Optional, Union

import h5py
import numpy as np
import rasterio
import rasterio.control
import rasterio.crs
import rasterio.transform
import rasterio.warp


class GCOMCFileError(Exception):
    """Raised when a HDF5 file is unexpected format."""

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
        cls, input_path: str, output_dir: str = ".", targets: Optional[list[str]] = None
    ) -> list[str]:
        """Converts a GCOM-C HDF5 file to GeoTIFF files.

        Args:
            input_path: Path to a GCOM-C HDF5 file.
            output_dir: Directory to save the GeoTIFF files.
            targets: Image data names to convert.

        Returns:
            List of paths to the converted GeoTIFF files.
        """
        with cls.open(input_path) as gcomc_file:
            return gcomc_file.save_as_geotiff(output_dir, targets=targets)

    @classmethod
    def convert_to_multiband_geotiff(cls, input_path: str, bands: list[str], output_path: Optional[str] = None) -> str:
        """Converts a GCOM-C HDF5 file to a multiband GeoTIFF file.

        Args:
            input_path: Path to a GCOM-C HDF5 file.
            bands: List of image data names for each band.
            output_path: Path to save the GeoTIFF file.

        Returns:
            Path to the converted GeoTIFF file.
        """
        with cls.open(input_path) as gcomc_file:
            return gcomc_file.save_as_multiband_geotiff(bands=bands, output_path=output_path)

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
    def attrs(self) -> dict[str, Union[int, float, str]]:
        """Global attributes."""
        return {
            k: v[0].decode() if isinstance(v[0], bytes) else v[0]
            for k, v in self.h5_file["Global_attributes"].attrs.items()
        }

    @property
    def granule_id(self) -> str:
        """Granule ID."""
        return Path(str(self.attrs["Product_file_name"])).stem

    @property
    def geometry_attrs(self) -> dict[str, Union[int, float, str]]:
        """Geometry data attributes."""
        return {
            k: v[0].decode() if isinstance(v[0], bytes) else v[0]
            for k, v in self.h5_file["Geometry_data"].attrs.items()
        }

    @property
    def geometry_data(self) -> dict[str, h5py.Dataset]:
        """Geometry data."""
        geometry_data = self.h5_file["Geometry_data"]

        if not isinstance(geometry_data, h5py.Group):
            raise GCOMCFileError(f"Geometry_data is not a group: {type(geometry_data)}")

        return {k: v for k, v in geometry_data.items()}

    @property
    def image_data(self) -> dict[str, h5py.Dataset]:
        image_data = self.h5_file["Image_data"]

        if not isinstance(image_data, h5py.Group):
            raise GCOMCFileError(f"Image_data is not a group: {type(image_data)}")

        return {k: v for k, v in image_data.items()}

    def save_as_geotiff(self, output_dir: str = ".", targets: Optional[list[str]] = None) -> list[str]:
        """Saves the file as GeoTIFF.

        Args:
            output_dir: Directory to save the GeoTIFF files.
            targets: Image data names to save. If not provided, all image data are saved.

        Returns:
            List of paths to the saved GeoTIFF files.
        """
        if targets is None:
            targets = [k for k in self.image_data.keys()]

        output_paths = []
        for image_data_name in targets:
            dataset = self.image_data[image_data_name]
            if dataset.ndim != 2:
                # Skip not 2D data, like Line_tai93.
                continue

            output_path = Path(output_dir) / f"{self.granule_id}-{image_data_name}.tif"
            output_paths.append(str(output_path))

            error_dn = dataset.attrs.get("Error_DN")
            if isinstance(error_dn, np.ndarray):
                error_dn = error_dn[0]

            crs, transform = self._build_crs_and_transform(dataset.shape)

            with rasterio.open(
                output_path,
                mode="w",
                driver="GTiff",
                width=dataset.shape[1],
                height=dataset.shape[0],
                count=1,
                dtype=dataset.dtype,
                crs=crs,
                transform=transform,
                nodata=error_dn,
            ) as dst:
                offset = dataset.attrs.get("Offset")
                if isinstance(offset, np.ndarray):
                    dst.offsets = (offset[0],)

                slope = dataset.attrs.get("Slope")
                if isinstance(slope, np.ndarray):
                    dst.scales = (slope[0],)

                dst.write(dataset, 1)

        return output_paths

    def save_as_multiband_geotiff(
        self,
        bands: list[str],
        output_path: Optional[Union[str, Path]] = None,
        nodata: Optional[Union[int, float]] = None,
    ) -> str:
        """Saves the file as a multiband GeoTIFF.

        Args:
            bands: List of image data names for each band.
            output_path: Path to save the GeoTIFF file.
            nodata: Nodata value.

        Returns:
            Path to the saved GeoTIFF file.
        """
        count = len(bands)
        datasets = [self.image_data[band] for band in bands]

        shape = datasets[0].shape
        for dataset in datasets[1:]:
            if dataset.shape != shape:
                raise ValueError("All bands must have the same shape.")

        if output_path is None:
            output_path = Path.cwd() / f"{self.granule_id}.tif"

        if nodata is None:
            # Set `nodata` if all bands have the same "Error_DN" values.
            error_dn_candidates = np.unique(np.array([dataset.attrs.get("Error_DN") for dataset in datasets]))
            if len(error_dn_candidates) == 1:
                nodata = error_dn_candidates[0]

        crs, transform = self._build_crs_and_transform(shape)

        dtype = np.find_common_type([dataset.dtype for dataset in datasets], [])

        with rasterio.open(
            output_path,
            mode="w",
            driver="GTiff",
            width=shape[1],
            height=shape[0],
            count=count,
            dtype=dtype,
            crs=crs,
            transform=transform,
            nodata=nodata,
        ) as dst:
            offsets = [0.0] * count
            scales = [1.0] * count

            for i, dataset in enumerate(datasets):
                offset = dataset.attrs.get("Offset")
                if isinstance(offset, np.ndarray):
                    offsets[i] = offset[0]

                slope = dataset.attrs.get("Slope")
                if isinstance(slope, np.ndarray):
                    scales[i] = slope[0]

                dst.write(dataset, i + 1)

            dst.offsets = offsets
            dst.scales = scales

        return str(output_path)

    def _build_crs_and_transform(self, shape: tuple[int, int]) -> tuple[rasterio.crs.CRS, rasterio.transform.Affine]:
        # https://shikisai.jaxa.jp/faq/faq0062.html?006

        geometry_attrs = self.geometry_attrs
        projection = self.geometry_attrs["Image_projection"]

        if projection == "L1B reference grid":
            crs = rasterio.CRS.from_epsg(4326)

            lat = self.geometry_data["Latitude"]
            lon = self.geometry_data["Longitude"]

            row_interval = shape[0] / (lat.shape[0] - 1)
            col_interval = shape[1] / (lat.shape[1] - 1)

            gcps = [
                rasterio.control.GroundControlPoint(
                    row=index[0] * row_interval,
                    col=index[1] * col_interval,
                    x=lon[index],
                    y=lat[index],
                )
                for index in np.ndindex(lat.shape)
            ]

            transform = rasterio.transform.from_gcps(gcps)

            return crs, transform

        elif projection == "EQA (sinusoidal equal area) projection from 0-deg longitude":
            crs = rasterio.CRS.from_authority("ESRI", 53008)

            (west, east), (north, south) = rasterio.warp.transform(  # type: ignore
                src_crs=rasterio.CRS.from_epsg(4326),
                dst_crs=crs,
                xs=[geometry_attrs["Upper_left_longitude"], geometry_attrs["Lower_right_longitude"]],
                ys=[geometry_attrs["Upper_left_latitude"], geometry_attrs["Lower_right_latitude"]],
            )

            transform = rasterio.transform.from_bounds(
                west=west,
                south=south,
                east=east,
                north=north,
                width=shape[1],
                height=shape[0],
            )

            return crs, transform

        elif projection == "Equal Rectangular projection":
            crs = rasterio.CRS.from_epsg(4326)
            transform = rasterio.transform.from_bounds(
                west=geometry_attrs["Upper_left_longitude"],
                south=geometry_attrs["Lower_right_latitude"],
                east=geometry_attrs["Lower_right_longitude"],
                north=geometry_attrs["Upper_left_latitude"],
                width=shape[1],
                height=shape[0],
            )
            return crs, transform

        else:
            raise NotImplementedError(f"Projection {projection} is not supported.")
