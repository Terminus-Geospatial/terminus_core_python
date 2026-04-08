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
        self.dataset = None
        self.bounds = None
        self.epsg_code = None
        self._transformer = None

        # Validate file exists
        if not self.file_path.exists():
            raise FileNotFoundError(f"GeoTIFF file not found: {self.file_path}")

    def _load_dataset(self):
        """Lazy load the GeoTIFF dataset."""
        if self.dataset is None:
            try:
                self.dataset = rasterio.open(self.file_path)
                self.bounds = self.dataset.bounds
                self.epsg_code = self.dataset.crs.to_epsg()
                logging.info(f"Loaded GeoTIFF: {self.file_path} (EPSG:{self.epsg_code})")
            except Exception as e:
                logging.error(f"Failed to load GeoTIFF {self.file_path}: {e}")
                raise

    def _get_transformer(self):
        """Get coordinate transformer for this dataset."""
        if self._transformer is None:
            self._load_dataset()
            self._transformer = Transformer()
        return self._transformer

    def contains(self, coord: Geographic) -> bool:
        """Check if this GeoTIFF contains data for the specified coordinate."""
        try:
            self._load_dataset()
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

            # Sample elevation at the transformed coordinates
            elevation_values = self.dataset.sample([(x, y)])

            # Convert generator to list if needed
            if hasattr(elevation_values, '__iter__') and not hasattr(elevation_values, '__len__'):
                elevation_values = list(elevation_values)

            if elevation_values is not None and len(elevation_values) > 0:
                elevation_value = elevation_values[0]

                # Check for nodata value
                if self.dataset.nodata is not None and elevation_value == self.dataset.nodata:
                    return None

                # Handle numpy array conversion
                if hasattr(elevation_value, 'item'):
                    elevation = float(elevation_value.item())
                else:
                    elevation = float(elevation_value)

                # Handle datum conversion if needed
                if target_datum is not None and target_datum != self.vertical_datum:
                    return self._convert_datum(elevation, target_datum, coord.latitude_deg, coord.longitude_deg)

                return elevation
            else:
                return None

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
                'width': self.dataset.width if self.dataset else None,
                'height': self.dataset.height if self.dataset else None,
            } if self.dataset else None,
        })
        return info

    def close(self):
        """Close the dataset to free resources."""
        if self.dataset is not None:
            self.dataset.close()
            self.dataset = None

    def __del__(self):
        """Ensure dataset is closed when object is destroyed."""
        self.close()


