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
#    File:    terrain_catalog.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Catalog for managing local GeoTIFF elevation data sources.
"""

import logging
import os
from pathlib import Path
from typing import Any

# Project Libraries
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.vdatum import Base as VBase
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.source import Base, GeoTIFF


class Catalog(Base):
    """Catalog for managing local GeoTIFF elevation data sources."""

    def __init__(
        self,
        catalog_root: str | Path | None = None,
        vertical_datum: VBase | None = None,
        interpolation: Interpolation_Method = Interpolation_Method.BILINEAR
    ):
        """
        Initialize terrain catalog.

        Args:
            catalog_root: Root directory containing GeoTIFF files. If None, uses TERRAIN_CATALOG_ROOT env var.
            vertical_datum: Default vertical datum for catalog sources
            interpolation: Interpolation method for elevation queries
        """
        super().__init__("Terrain Catalog", vertical_datum, interpolation)

        if catalog_root is None:
            catalog_root = os.environ.get('TERRAIN_CATALOG_ROOT')
            if catalog_root is None:
                raise ValueError("catalog_root must be provided or TERRAIN_CATALOG_ROOT environment variable must be set")

        self.catalog_root = Path(catalog_root)
        self.source_cache: dict[Path, GeoTIFF] = {}
        self.max_memory_mb = 500  # Maximum memory for cached tiles
        self.logger = logging.getLogger(__name__)

        # Discover and index GeoTIFF files
        self._discover_sources()

    def _discover_sources(self):
        """Discover all GeoTIFF files in the catalog directory.

        Each file is instantiated as a GeoTIFF, which reads the CRS and bounds
        from the file header only — no raster data is loaded at this stage.
        """
        if not self.catalog_root.exists():
            self.logger.warning(f"Catalog directory does not exist: {self.catalog_root}")
            return

        for tif_file in self.catalog_root.rglob("*.tif"):
            try:
                source = GeoTIFF(tif_file, self.vertical_datum, self.interpolation)
                self.source_cache[tif_file] = source
            except Exception as e:
                self.logger.warning(f"Could not index GeoTIFF {tif_file}: {e}")

        self.logger.info(f"Discovered {len(self.source_cache)} GeoTIFF files in {self.catalog_root}")

    def contains(self, coord: Geographic) -> bool:
        """
        Check if any source in the catalog contains the specified coordinate.

        Args:
            coord: Geographic coordinate to check

        Returns:
            True if any source has data for this coordinate, False otherwise
        """
        return any(source.contains(coord) for source in self.source_cache.values())

    def elevation_meters(self, coord: Geographic, target_datum: VBase | None = None) -> float | None:
        """
        Get elevation from the catalog.

        Args:
            coord: Geographic coordinate to query
            target_datum: Target vertical datum for the elevation (optional)

        Returns:
            Elevation in meters in target datum (or source datum if None),
            or None if no data found
        """
        for source in self.source_cache.values():
            if source.contains(coord):
                elevation = source.elevation_meters(coord, target_datum)
                if elevation is not None:
                    return elevation

        return None

    def get_sources_for_coordinate(self, coord: Geographic) -> list[GeoTIFF]:
        """Get all sources that contain the given coordinate."""
        return [source for source in self.source_cache.values() if source.contains(coord)]

    def info(self) -> dict[str, Any]:
        """Get detailed information about this terrain catalog."""
        info = super().info()
        info.update({
            'catalog_root': str(self.catalog_root),
            'total_sources': len(self.source_cache),
            'sources': [
                {
                    'name': source.name,
                    'file_path': str(source.file_path),
                    'bounds': source.bounds._asdict() if hasattr(source, 'bounds') and source.bounds else None,
                    'epsg_code': source.epsg_code if hasattr(source, 'epsg_code') else None
                }
                for source in self.source_cache.values()
            ]
        })
        return info


