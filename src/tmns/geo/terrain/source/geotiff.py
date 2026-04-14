#**************************** INTELLECTUAL PROPERTY RIGHTS ****************************#
#*                                                                                    *#
#*                           Copyright (c) 2026 Terminus LLC                          *#
#*                                                                                    *#
#*                                All Rights Reserved.                                *#
#*                                                                                    *#
#*          Use of this source code is governed by LICENSE in the repo root.          *#
#*                                                                                    *#
#**************************** INTELLECTUAL PROPERTY RIGHTS ****************************#
#
#    File:    geotiff.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
GeoTIFF elevation source implementation.

Provides elevation data from GeoTIFF files with lazy loading and caching.
"""

# Python Standard Libraries
import logging
from pathlib import Path
from typing import Any

# Third-Party Libraries
import rasterio

# Project Libraries
from tmns.geo.coord import Geographic, Transformer
from tmns.geo.coord.vdatum import Base as VBase
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.source.base import Base


class GeoTIFF(Base):
    """GeoTIFF file elevation source with lazy loading and caching."""

    def __init__(
        self,
        file_path: str | Path,
        vertical_datum: VBase | None = None,
        interpolation: Interpolation_Method = Interpolation_Method.BILINEAR
    ):
        """
        Initialize GeoTIFF elevation source.

        Args:
            file_path: Path to GeoTIFF file
            vertical_datum: Vertical datum of the elevation data. Defaults to EGM96 for DTED/SRTM.
            interpolation: Interpolation method for elevation queries
        """
        super().__init__(f"GeoTIFF ({Path(file_path).name})", vertical_datum, interpolation)

        self.file_path = Path(file_path)
        self._transformer = None
        self._data = None          # Full raster band loaded into RAM
        self._transform = None     # Affine transform for pixel lookups
        self._nodata = None

        # Validate file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"GeoTIFF file not found: {self.file_path}")

        # Load CRS and bounds from header only — no raster data read
        with rasterio.open(self.file_path) as ds:
            self.bounds = ds.bounds
            self.epsg_code = ds.crs.to_epsg()

    def _load_dataset(self):
        """Lazy load the full raster into RAM, then close the file handle."""
        if self._data is None:
            try:
                with rasterio.open(self.file_path) as ds:
                    self._data = ds.read(1).astype(float)
                    self._transform = ds.transform
                    self._nodata = ds.nodata
                logging.info(f"Loaded GeoTIFF: {self.file_path} (EPSG:{self.epsg_code})")
            except Exception as e:
                logging.error(f"Failed to load GeoTIFF {self.file_path}: {e}")
                raise

    def _get_transformer(self):
        """Get coordinate transformer for this dataset."""
        if self._transformer is None:
            self._transformer = Transformer()
        return self._transformer

    def contains(self, coord: Geographic) -> bool:
        """Check if this GeoTIFF contains data for the specified coordinate."""
        try:
            transformer = self._get_transformer()

            # Transform geographic coordinate to dataset CRS
            transformed_coord = transformer.transform(coord, f"EPSG:{self.epsg_code}")
            x, y = transformed_coord.longitude_deg, transformed_coord.latitude_deg

            # Check if point is within bounds
            return (self.bounds.left <= x <= self.bounds.right and
                    self.bounds.bottom <= y <= self.bounds.top)
        except Exception as e:
            logging.error(f"Error checking containment: {e}")
            return False

    def elevation_meters(self, coord: Geographic, target_datum: VBase | None = None) -> float | None:
        """
        Get elevation at the specified geographic coordinate.

        Args:
            coord: Geographic coordinate (latitude, longitude, altitude)
            target_datum: Target vertical datum for the elevation (optional)

        Returns:
            Elevation in meters in the target datum (or source datum if None),
            or None if no data available
        """
        try:
            self._load_dataset()
            transformer = self._get_transformer()

            # Transform geographic coordinate to dataset CRS
            transformed_coord = transformer.transform(coord, f"EPSG:{self.epsg_code}")
            x, y = transformed_coord.longitude_deg, transformed_coord.latitude_deg

            # Convert geographic coordinates to pixel row/col via affine transform
            col, row = ~self._transform * (x, y)
            row, col = int(row), int(col)

            # Bounds check
            if row < 0 or row >= self._data.shape[0] or col < 0 or col >= self._data.shape[1]:
                return None

            elevation = float(self._data[row, col])

            # Check for nodata
            if self._nodata is not None and elevation == self._nodata:
                return None

            # Handle datum conversion if needed
            if target_datum is not None and target_datum != self.vertical_datum:
                return self._convert_datum(elevation, target_datum, coord.latitude_deg, coord.longitude_deg)

            return elevation

        except Exception as e:
            logging.error(f"Error getting elevation from GeoTIFF: {e}")
            return None

    def info(self) -> dict[str, Any]:
        """Get detailed information about this GeoTIFF source."""
        info = super().info()
        info.update({
            'file_path': str(self.file_path),
            'file_size': self.file_path.stat().st_size if self.file_path.exists() else 0,
            'epsg_code': self.epsg_code,
            'bounds': {
                'left': self.bounds.left if self.bounds else None,
                'right': self.bounds.right if self.bounds else None,
                'top': self.bounds.top if self.bounds else None,
                'bottom': self.bounds.bottom if self.bounds else None,
            },
            'resolution': {
                'rows': self._data.shape[0] if self._data is not None else None,
                'cols': self._data.shape[1] if self._data is not None else None,
            } if self._data is not None else None,
        })
        return info

    def close(self):
        """Release the in-memory raster data."""
        self._data = None
        self._transform = None
        self._nodata = None


