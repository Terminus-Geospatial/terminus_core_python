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
#    File:    web_mercator.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Web Mercator coordinate implementation.
"""

# Python Standard Libraries
from dataclasses import dataclass
from typing import Union

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type
from tmns.geo.coord.epsg import EPSG_Manager


@dataclass
class Web_Mercator:
    """Web Mercator coordinate (easting, northing, elevation)."""
    easting_m: float
    northing_m: float
    altitude_m: float | None = None
    crs: str = "EPSG:3857"  # Web Mercator coordinate system

    @staticmethod
    def create(easting_m: float, northing_m: float, alt_m: float | None = None) -> 'Web_Mercator':
        """Create a Web Mercator coordinate."""
        return Web_Mercator(easting_m=easting_m, northing_m=northing_m, crs="EPSG:3857", altitude_m=alt_m)

    def type(self) -> Coordinate_Type:
        """Get the coordinate type."""
        return Coordinate_Type.WEB_MERCATOR

    def to_tuple(self) -> tuple[float, float]:
        """Convert to (easting, northing) tuple."""
        return (self.easting_m, self.northing_m)

    def to_3d_tuple(self) -> tuple[float, float, float]:
        """Convert to (easting, northing, elevation) tuple."""
        return (self.easting_m, self.northing_m, self.altitude_m or 0.0)

    def __str__(self) -> str:
        """String representation."""
        if self.altitude_m is not None:
            return f"({self.easting_m:.2f}, {self.northing_m:.2f}, {self.altitude_m:.1f}m) [{self.crs}]"
        return f"({self.easting_m:.2f}, {self.northing_m:.2f}) [{self.crs}]"

    def to_epsg(self) -> int:
        """Get EPSG code for this coordinate."""
        return EPSG_Manager.WEB_MERCATOR

    @staticmethod
    def distance(coord1: Web_Mercator, coord2: Web_Mercator) -> float:
        """Calculate Euclidean distance between two Web Mercator coordinates.

        Calculates the straight-line Euclidean distance between two points
        in the Web Mercator coordinate system.

        Args:
            coord1: First Web Mercator coordinate
            coord2: Second Web Mercator coordinate

        Returns:
            Distance in meters between the two coordinates.
            Note: This distance is in Web Mercator projection space, not
            true great circle distance on the Earth's surface.

        Raises:
            ValueError: If coordinates are in different coordinate systems
        """
        # Web Mercator coordinates should all use the same CRS (EPSG:3857)
        # But we validate for consistency
        if coord1.crs != coord2.crs:
            raise ValueError(f"Cannot calculate distance between coordinates in different coordinate systems: {coord1.crs} vs {coord2.crs}")

        # Calculate differences
        dx = coord2.easting_m - coord1.easting_m
        dy = coord2.northing_m - coord1.northing_m
        dz = (coord2.altitude_m or 0) - (coord1.altitude_m or 0)

        # Euclidean distance
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        return distance

    @staticmethod
    def bearing(from_coord: Web_Mercator, to_coord: Web_Mercator, as_deg: bool = True) -> float:
        """Calculate bearing from one Web Mercator coordinate to another.

        Args:
            from_coord: Starting Web Mercator coordinate
            to_coord: Ending Web Mercator coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, π/2 = east, π = south, 3π/2 = west)
            Range is always [0, 360] degrees or [0, 2π] radians regardless of coordinate positions.

        Raises:
            ValueError: If coordinates are in different coordinate systems
        """
        # Web Mercator coordinates should all use the same CRS (EPSG:3857)
        # But we validate for consistency
        if from_coord.crs != to_coord.crs:
            raise ValueError(f"Cannot calculate bearing between coordinates in different coordinate systems: {from_coord.crs} vs {to_coord.crs}")

        # Calculate bearing in Web Mercator coordinate system
        dx = to_coord.easting_m - from_coord.easting_m
        dy = to_coord.northing_m - from_coord.northing_m

        bearing = np.arctan2(dx, dy)  # Note: dx/easting, dy/northing for bearing

        # Normalize to [0, 2π] radians
        bearing = (bearing + 2 * np.pi) % (2 * np.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = np.degrees(bearing)

        return bearing


__all__ = [
    'Web_Mercator',
]
