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
- Singleton pattern for global access
"""

# Python Standard Libraries
import logging
import os
import pickle
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Project Libraries
from tmns.geo.coord import Transformer, Geographic, Coordinate, Type
from tmns.geo.terrain.source import Base, GeoTIFF
from tmns.geo.terrain.elevation_point import Elevation_Point
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.catalog import Catalog
from tmns.geo.coord.vdatum import Base as VBase, ELIPSOIDAL_DATUM


@dataclass
class Manager:
    """
    Terrain elevation manager with caching and coordinate transformations.

    The Manager provides a unified interface for querying elevation data from
    multiple sources, handling coordinate transformations, vertical datum conversions,
    and intelligent caching for optimal performance.

    Attributes:
        sources: List of elevation data sources (GeoTIFF, Flat, etc.)
        cache_enabled: Whether to enable elevation result caching
        interpolation: Default interpolation method for elevation queries
        default_vertical_datum: Default vertical datum for output elevations
        cache_file: Path to persistent cache file
        elevation_cache: In-memory cache of elevation results
        coord_transformer: Coordinate transformation utility
    """

    sources: list[Base]
    cache_enabled: bool = True
    interpolation: Interpolation_Method = Interpolation_Method.BILINEAR
    default_vertical_datum: VBase | None = None
    cache_file: Path = field(default_factory=lambda: Path(tempfile.gettempdir()) / "terminus_core_python" / "elevation_cache.pkl")
    elevation_cache: dict[str, Elevation_Point] = field(default_factory=dict)
    coord_transformer: Transformer = field(default_factory=Transformer)

    # Class variable for singleton instance
    _instance: Manager | None = None

    def __post_init__(self):
        """Initialize manager after dataclass creation."""
        # Ensure cache directory exists
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # Configure sources with manager settings
        self._configure_sources()

        # Load cache if enabled
        if self.cache_enabled and self.cache_file.exists():
            self._load_cache()

    def _configure_sources(self):
        """Configure all sources with manager settings."""
        for source in self.sources:
            if hasattr(source, 'interpolation'):
                source.interpolation = self.interpolation

    @classmethod
    def global_instance(cls) -> 'Manager':
        """Get the global singleton terrain manager instance.

        Returns:
            The singleton Manager instance, creating it if necessary
        """
        if cls._instance is None:
            cls._instance = cls.create_default()
        return cls._instance

    @classmethod
    def create_default(cls, cache_enabled: bool = True,
                      interpolation: Interpolation_Method = Interpolation_Method.BILINEAR,
                      default_vertical_datum: VBase | None = None) -> 'Manager':
        """Create a default terrain manager with catalog sources.

        Args:
            cache_enabled: Whether to enable elevation caching
            interpolation: Default interpolation method for queries
            default_vertical_datum: Default vertical datum for outputs

        Returns:
            Manager instance with catalog sources

        Raises:
            ValueError: If no terrain sources are available
        """
        try:
            catalog = Catalog()
            return cls([catalog], cache_enabled, interpolation, default_vertical_datum)
        except Exception as e:
            raise ValueError("No terrain sources available. Please ensure GeoTIFF files are in the catalog directory.")

    @classmethod
    def create_catalog_only(cls, catalog_root: str | Path | None = None,
                           cache_enabled: bool = True,
                           interpolation: Interpolation_Method = Interpolation_Method.BILINEAR,
                           default_vertical_datum: VBase | None = None) -> 'Manager':
        """Create a terrain manager with only catalog sources.

        Args:
            catalog_root: Path to catalog directory containing GeoTIFF files
            cache_enabled: Whether to enable elevation caching
            interpolation: Default interpolation method for queries
            default_vertical_datum: Default vertical datum for outputs

        Returns:
            Manager instance with catalog sources

        Raises:
            ValueError: If no terrain sources are found in catalog
        """
        catalog = Catalog(catalog_root)
        if not catalog.sources:
            raise ValueError(f"No terrain sources found in catalog: {catalog.catalog_root}")
        return cls([catalog], cache_enabled, interpolation, default_vertical_datum)

    @classmethod
    def get_default(cls) -> 'Manager':
        """Get the global default terrain manager instance (alias for global_instance)."""
        return cls.global_instance()

    @classmethod
    def reset_global_instance(cls):
        """Reset the global singleton instance.

        Useful for testing and when you need to reinitialize the manager
        with different configuration.
        """
        cls._instance = None

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

    @staticmethod
    def _cache_key(coord: Coordinate) -> str:
        """Generate consistent cache key for any coordinate type.

        Args:
            coord: Input coordinate of any type

        Returns:
            String cache key based on geographic coordinates
        """
        # Convert to geographic coordinates first
        transformer = Transformer()

        if coord.type() == Type.GEOGRAPHIC:
            geo = coord
        elif coord.type() == Type.UTM:
            geo = transformer.utm_to_geo(coord)
        elif coord.type() == Type.WEB_MERCATOR:
            geo = transformer.web_mercator_to_geo(coord)
        elif coord.type() == Type.UPS:
            geo = transformer.ups_to_geo(coord)
        elif coord.type() == Type.ECEF:
            geo = transformer.ecef_to_geo(coord)
        else:
            # Other coordinate types - use unique identifier
            return f"{coord.type().name}_{id(coord)}"

        return f"{geo.latitude_deg:.6f},{geo.longitude_deg:.6f}"

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

        # Check cache first
        cache_key = self._cache_key(geo_coord)

        if self.cache_enabled and cache_key in self.elevation_cache:
            cached_point = self.elevation_cache[cache_key]

            # Convert to target datum if needed
            target_datum = vertical_datum or self.default_vertical_datum
            if target_datum and cached_point.vertical_datum != target_datum:
                return cached_point.to_datum(target_datum)
            return cached_point

        # Query sources
        point = self._query_sources(geo_coord)
        if point is not None:
            # Cache the result
            if self.cache_enabled:
                self.elevation_cache[cache_key] = point
                self._save_cache()

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

    def clear_cache(self):
        """Clear elevation cache from memory and disk."""
        self.elevation_cache.clear()
        if self.cache_file.exists():
            self.cache_file.unlink()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics.

        Returns:
            Dictionary containing cache statistics and manager configuration
        """
        return {
            'cached_points': len(self.elevation_cache),
            'cache_file': str(self.cache_file),
            'cache_size_mb': self.cache_file.stat().st_size / (1024 * 1024) if self.cache_file.exists() else 0,
            'cache_enabled': self.cache_enabled,
            'sources': [source.name for source in self.sources],
            'num_sources': len(self.sources),
            'default_vertical_datum': self.default_vertical_datum.name if self.default_vertical_datum else None,
            'interpolation': self.interpolation.name
        }

    def _load_cache(self):
        """Load elevation cache from file."""
        try:
            with open(self.cache_file, 'rb') as f:
                self.elevation_cache = pickle.load(f)
        except Exception as e:
            # Handle any pickle errors including class name changes
            logging.warning(f"Could not load cache due to: {e}. Starting with empty cache.")
            self.elevation_cache = {}
            # Remove the problematic cache file
            try:
                self.cache_file.unlink()
                logging.info("Removed problematic cache file")
            except:
                pass

    def _save_cache(self):
        """Save elevation cache to file."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.elevation_cache, f)
        except (IOError, pickle.PickleError) as e:
            logging.warning(f"Could not save elevation cache: {e}")


