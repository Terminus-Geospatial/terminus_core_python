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
#    File:    manager.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Terrain elevation manager with caching and vertical datum support.

This module provides a unified interface for querying elevation data from multiple
sources, with support for coordinate transformations, vertical datum conversions,
and intelligent caching for performance optimization.

Key Features:
- Multiple elevation source support (GeoTIFF, Flat, etc.)
- Automatic coordinate type conversion
- Vertical datum transformations
- Persistent caching for performance
"""

# Python Standard Libraries
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Project Libraries
from tmns.geo.coord import Coordinate, Geographic, Transformer, Type
from tmns.geo.coord.vdatum import Base as VBase
from tmns.geo.terrain.catalog import Catalog
from tmns.geo.terrain.elevation_point import Elevation_Point
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.source import Base, GeoTIFF

# Module-level singleton instance for convenience functions
_default_manager: 'Manager' | None = None


@dataclass
class Manager:
    """
    Terrain elevation manager with caching and coordinate transformations.

    The Manager provides a unified interface for querying elevation data from
    multiple sources, handling coordinate transformations, vertical datum conversions,
    and intelligent caching for optimal performance.

    Attributes:
        sources: List of elevation data sources (GeoTIFF, Flat, etc.)
        interpolation: Default interpolation method for elevation queries
        default_vertical_datum: Default vertical datum for output elevations
        coord_transformer: Coordinate transformation utility
    """

    sources: list[Base]
    interpolation: Interpolation_Method = Interpolation_Method.BILINEAR
    default_vertical_datum: VBase | None = None
    coord_transformer: Transformer = field(default_factory=Transformer)

    def __post_init__(self):
        """Initialize manager after dataclass creation."""
        self._configure_sources()

    def _configure_sources(self):
        """Configure all sources with manager settings."""
        for source in self.sources:
            if hasattr(source, 'interpolation'):
                source.interpolation = self.interpolation

    @classmethod
    def create_default(cls, interpolation: Interpolation_Method = Interpolation_Method.BILINEAR,
                      default_vertical_datum: VBase | None = None) -> 'Manager':
        """Create a default terrain manager with catalog sources.

        Args:
            interpolation: Default interpolation method for queries
            default_vertical_datum: Default vertical datum for outputs

        Returns:
            Manager instance with catalog sources

        Raises:
            ValueError: If no terrain sources are available
        """
        try:
            catalog = Catalog()
            return cls([catalog], interpolation, default_vertical_datum)
        except Exception:
            raise ValueError("No terrain sources available. Please ensure GeoTIFF files are in the catalog directory.") from None

    @classmethod
    def create_catalog_only(cls, catalog_root: str | Path | None = None,
                           interpolation: Interpolation_Method = Interpolation_Method.BILINEAR,
                           default_vertical_datum: VBase | None = None) -> 'Manager':
        """Create a terrain manager with only catalog sources.

        Args:
            catalog_root: Path to catalog directory containing GeoTIFF files
            interpolation: Default interpolation method for queries
            default_vertical_datum: Default vertical datum for outputs

        Returns:
            Manager instance with catalog sources

        Raises:
            ValueError: If no terrain sources are found in catalog
        """
        catalog = Catalog(catalog_root)
        if not catalog.source_paths:
            raise ValueError(f"No terrain sources found in catalog: {catalog.catalog_root}")
        return cls([catalog], interpolation, default_vertical_datum)

    def add_local_dem(self, dem_file: str | Path, vertical_datum: VBase | None = None):
        """Add a local DEM file as a high-priority elevation source.

        Args:
            dem_file: Path to GeoTIFF DEM file
            vertical_datum: Vertical datum of the DEM data

        Note:
            Local DEMs are added to the front of the sources list,
            giving them priority over catalog sources.
        """
        try:
            local_source = GeoTIFF(dem_file, vertical_datum)
            self.sources.insert(0, local_source)  # Prioritize local DEM
        except Exception as e:
            logging.warning(f"Could not add local DEM {dem_file}: {e}")

    def _query_sources(self, coord: Geographic) -> Elevation_Point | None:
        """
        Query all elevation sources for elevation data.

        Args:
            coord: Geographic coordinate to query

        Returns:
            Elevation_Point with full metadata or None if no data found
        """
        # Try each source in order
        for source in self.sources:
            try:
                elevation = source.elevation_meters(coord)
                if elevation is not None:
                    # Create elevation point with metadata
                    return Elevation_Point(
                        coord=Geographic(coord.latitude_deg, coord.longitude_deg, elevation),
                        source=source.name,
                        vertical_datum=source.vertical_datum
                    )

            except Exception as e:
                logging.warning(f"Elevation source {source.name} failed: {e}")
                continue

        return None

    def elevation(self, coord: Coordinate, vertical_datum: VBase | None = None) -> float | None:
        """
        Get elevation for any coordinate type in specified vertical datum.

        Args:
            coord: Input coordinate (any type)
            vertical_datum: Target vertical datum for output. If None, uses manager default.

        Returns:
            Elevation in target vertical datum (meters) or None if not found
        """
        elevation_point = self.elevation_point(coord, vertical_datum)
        if elevation_point is not None:
            return elevation_point.coord.altitude_m
        return None

    def elevation_point(self, coord: Coordinate, vertical_datum: VBase | None = None) -> Elevation_Point | None:
        """
        Get elevation point with full metadata for any coordinate type.

        Args:
            coord: Input coordinate (any type)
            vertical_datum: Target vertical datum for output. If None, uses manager default.

        Returns:
            Elevation point with metadata in target vertical datum or None if not found
        """
        # Convert to geographic coordinates first
        if coord.type() == Type.GEOGRAPHIC:
            geo_coord = coord
        else:
            geo_coord = self.coord_transformer.convert(coord, Type.GEOGRAPHIC)

        # Query sources
        point = self._query_sources(geo_coord)
        if point is not None:
            # Convert to target datum if needed
            target_datum = vertical_datum or self.default_vertical_datum
            if target_datum and point.vertical_datum != target_datum:
                return point.to_datum(target_datum)
            return point

        return None


    def get_elevation_point(self, latitude: float, longitude: float,
                           vertical_datum: VBase | None = None) -> Elevation_Point | None:
        """Get detailed elevation point with metadata.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            vertical_datum: Target vertical datum for output

        Returns:
            Elevation point with metadata or None if not found
        """
        coord = Geographic(latitude, longitude)
        return self.elevation_point(coord, vertical_datum)

    def get_info(self) -> dict[str, Any]:
        """Get information about manager configuration.

        Returns:
            Dictionary containing manager configuration
        """
        return {
            'sources': [source.name for source in self.sources],
            'num_sources': len(self.sources),
            'default_vertical_datum': self.default_vertical_datum.name if self.default_vertical_datum else None,
            'interpolation': self.interpolation.name
        }


def get_default_manager() -> Manager:
    """Get the default terrain manager instance (singleton pattern for caching).

    Returns:
        The singleton Manager instance, creating it if necessary
    """
    global _default_manager
    if _default_manager is None:
        _default_manager = Manager.create_default()
    return _default_manager

