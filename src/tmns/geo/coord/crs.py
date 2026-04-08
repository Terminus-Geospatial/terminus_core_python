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
#    File:    crs.py
#    Author:  Marvin Smith
#    Date:    04/07/2026
#
"""
Coordinate Reference System (CRS) implementation.

This module provides a CRS class that encapsulates coordinate reference system
information, replacing string-based CRS handling with a type-safe object
approach. CRS objects wrap EPSG codes and provide access to datum and
projection information.

The CRS class follows GDAL's modern terminology (CRS vs SRS) and provides
a clean interface for working with different coordinate reference systems.
"""

# Python Standard Libraries
from dataclasses import dataclass
from typing import Any

# Third-Party Libraries
import pyproj

# Project Libraries
from tmns.geo.coord.epsg import Manager, Code
from tmns.geo.coord.types import Type


@dataclass
class CRS:
    """
    Coordinate Reference System (CRS) object.

    Represents a complete coordinate reference system including horizontal datum,
    projection, and vertical datum information. This replaces string-based
    CRS handling with a type-safe object approach.

    Attributes:
        epsg_code: EPSG code identifier for the CRS
        _pyproj_crs: Lazy-loaded pyproj CRS object
        _definition: Lazy-loaded CRS definition string
    """
    epsg_code: int
    _pyproj_crs: pyproj.CRS = None  # Lazy-loaded pyproj CRS object
    _definition: str = None  # Lazy-loaded CRS definition

    def __post_init__(self):
        """Validate EPSG code and prepare for lazy loading."""
        if not isinstance(self.epsg_code, int):
            raise TypeError(f"EPSG code must be an integer, got {type(self.epsg_code)}")

        if self.epsg_code <= 0:
            raise ValueError(f"EPSG code must be positive, got {self.epsg_code}")

    @property
    def pyproj_crs(self) -> pyproj.CRS:
        """
        Get pyproj CRS object (lazy-loaded).

        Returns:
            pyproj CRS object for detailed CRS information
        """
        if self._pyproj_crs is None:
            self._pyproj_crs = pyproj.CRS.from_epsg(self.epsg_code)
        return self._pyproj_crs

    @property
    def definition(self) -> str:
        """
        Get CRS definition string (lazy-loaded).

        Returns:
            CRS definition string from pyproj
        """
        if self._definition is None:
            self._definition = str(self.pyproj_crs)
        return self._definition

    # ============================================================================
    # CLASS METHODS
    # ============================================================================

    @classmethod
    def from_epsg(cls, epsg_code: int) -> CRS:
        """
        Create CRS from EPSG code.

        Args:
            epsg_code: EPSG code identifier

        Returns:
            CRS instance
        """
        return cls(epsg_code=epsg_code)

    @classmethod
    def utm_zone(cls, zone: int, hemisphere: str = 'N') -> CRS:
        """
        Create UTM zone CRS.

        Args:
            zone: UTM zone number (1-60)
            hemisphere: 'N' for northern, 'S' for southern

        Returns:
            CRS instance for the specified UTM zone

        Raises:
            ValueError: If zone is invalid or hemisphere is not 'N'/'S'
        """
        if not 1 <= zone <= 60:
            raise ValueError(f"UTM zone must be 1-60, got {zone}")

        if hemisphere not in ['N', 'S']:
            raise ValueError(f"Hemisphere must be 'N' or 'S', got {hemisphere}")

        if hemisphere == 'N':
            epsg_code = 32600 + zone
        else:
            epsg_code = 32700 + zone

        return cls(epsg_code=epsg_code)

    @classmethod
    def web_mercator(cls) -> CRS:
        """
        Create Web Mercator CRS.

        Returns:
            CRS instance for Web Mercator (EPSG:3857)
        """
        return cls(epsg_code=Code.WEB_MERCATOR)

    @classmethod
    def ecef(cls) -> CRS:
        """
        Create ECEF CRS.

        Returns:
            CRS instance for ECEF (EPSG:4978)
        """
        return cls(epsg_code=Code.ECEF)

    @classmethod
    def wgs84_geographic(cls) -> CRS:
        """
        Create WGS84 geographic CRS.

        Returns:
            CRS instance for WGS84 geographic (EPSG:4326)
        """
        return cls(epsg_code=Code.WGS84)

    # ============================================================================
    # PROPERTIES
    # ============================================================================

    @property
    def coordinate_type(self) -> str:
        """
        Get coordinate type.

        Returns:
            Coordinate type string (geographic, projected, etc.)
        """
        if self.pyproj_crs.is_geographic:
            return "geographic"
        elif self.pyproj_crs.is_projected:
            return "projected"
        elif self.pyproj_crs.is_geocentric:
            return "geocentric"
        elif self.pyproj_crs.is_vertical:
            return "vertical"
        else:
            return "unknown"

    @property
    def unit(self) -> str:
        """
        Get coordinate unit.

        Returns:
            Unit string (meter, degree, etc.)
        """
        # Use pyproj to get accurate unit information
        if self.pyproj_crs.is_geographic:
            # Geographic coordinates use angular units
            if hasattr(self.pyproj_crs, 'angular_unit'):
                return self.pyproj_crs.angular_unit_name.lower()
            else:
                return "degree"  # Default for geographic
        else:
            # Projected coordinates use linear units
            if hasattr(self.pyproj_crs, 'linear_unit'):
                return self.pyproj_crs.linear_unit_name.lower()
            else:
                return "meter"  # Default for projected

    @property
    def projection(self) -> str:
        """
        Get projection type.

        Returns:
            Projection type string
        """
        if self.pyproj_crs.is_geographic:
            return "geographic"
        elif self.pyproj_crs.is_geocentric:
            return "geocentric"
        elif self.pyproj_crs.is_vertical:
            return "vertical"
        elif self.pyproj_crs.is_projected:
            # Get projection name from pyproj
            if hasattr(self.pyproj_crs, 'name'):
                proj_name = self.pyproj_crs.name.lower()
                # Clean up common projection names
                if "mercator" in proj_name:
                    return "web_mercator"
                elif "utm" in proj_name:
                    return "utm"
                elif "polar stereographic" in proj_name or "ups" in proj_name:
                    return "ups"
                else:
                    return proj_name
            else:
                return "projected"
        else:
            return "unknown"

    @property
    def vertical_datum(self) -> 'VDatumBase':
        """
        Get vertical datum.

        Returns:
            Vertical datum object if available, None otherwise
        """
        if Code.is_vertical(self.epsg_code):
            return Manager.get_vertical_datum(self.epsg_code)
        return None

    @property
    def horizontal_datum(self) -> str:
        """
        Get horizontal datum.

        Returns:
            Horizontal datum string
        """
        # Use pyproj to get accurate datum information
        if hasattr(self.pyproj_crs, 'datum_name'):
            return self.pyproj_crs.datum_name
        elif hasattr(self.pyproj_crs, 'ellipsoid_name'):
            return self.pyproj_crs.ellipsoid_name
        else:
            # Fallback to common datums
            if self.epsg_code in [Code.WGS84, Code.WEB_MERCATOR] or Code.is_utm_zone(self.epsg_code):
                return "WGS84"
            elif self.epsg_code == Code.ECEF:
                return "WGS84"
            else:
                return "unknown"

    # ============================================================================
    # COMPARISON METHODS
    # ============================================================================

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another CRS.

        Args:
            other: Object to compare against

        Returns:
            True if EPSG codes are identical, False otherwise
        """
        if not isinstance(other, CRS):
            return False
        return self.epsg_code == other.epsg_code

    def __hash__(self) -> int:
        """
        Make CRS hashable for use in sets and as dictionary keys.

        Returns:
            Hash value based on EPSG code
        """
        return hash(self.epsg_code)

    def copy(self) -> CRS:
        """
        Create a copy of this CRS.

        Returns:
            New CRS instance with identical values
        """
        return CRS(epsg_code=self.epsg_code)

    # ============================================================================
    # STRING METHODS
    # ============================================================================

    def __str__(self) -> str:
        """
        String representation of the CRS.

        Returns:
            Human-readable string representation
        """
        return f"CRS(EPSG:{self.epsg_code})"

    def __repr__(self) -> str:
        """
        Detailed string representation of the CRS.

        Returns:
            Detailed string representation
        """
        return f"CRS(epsg_code={self.epsg_code})"

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def is_geographic(self) -> bool:
        """
        Check if this is a geographic CRS.

        Returns:
            True if geographic, False otherwise
        """
        return Code.is_geographic(self.epsg_code)

    def is_projected(self) -> bool:
        """
        Check if this is a projected CRS.

        Returns:
            True if projected, False otherwise
        """
        return Code.is_projected(self.epsg_code)

    def is_utm_zone(self) -> bool:
        """
        Check if this is a UTM zone CRS.

        Returns:
            True if UTM zone, False otherwise
        """
        return Code.is_utm_zone(self.epsg_code)

    def is_vertical(self) -> bool:
        """
        Check if this is a vertical CRS.

        Returns:
            True if vertical, False otherwise
        """
        return Code.is_vertical(self.epsg_code)

    def get_utm_zone_info(self) -> tuple[int, str]:
        """
        Get UTM zone information if this is a UTM CRS.

        Returns:
            Tuple of (zone_number, hemisphere)

        Raises:
            ValueError: If this is not a UTM CRS
        """
        if not self.is_utm_zone():
            raise ValueError(f"CRS {self.epsg_code} is not a UTM zone")

        if 32601 <= self.epsg_code <= 32660:
            zone = self.epsg_code - 32600
            hemisphere = 'N'
        elif 32701 <= self.epsg_code <= 32760:
            zone = self.epsg_code - 32700
            hemisphere = 'S'
        else:
            raise ValueError(f"Invalid UTM EPSG code: {self.epsg_code}")

        return zone, hemisphere


