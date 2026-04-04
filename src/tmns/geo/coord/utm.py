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
#    File:    utm.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
UTM coordinate implementation.
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
class UTM:
    """UTM coordinate (easting, northing, elevation)."""
    easting_m: float
    northing_m: float
    altitude_m: float | None = None
    crs: str = "EPSG:4326"  # Default to WGS84, should be set to appropriate UTM zone

    @staticmethod
    def create(easting_m: float, northing_m: float, crs: str = "EPSG:4326", alt_m: float | None = None) -> 'UTM':
        """Create a UTM coordinate."""
        return UTM(easting_m=easting_m, northing_m=northing_m, crs=crs, altitude_m=alt_m)

    def type(self) -> Coordinate_Type:
        """Get the coordinate type."""
        return Coordinate_Type.UTM

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
        return EPSG_Manager.to_epsg_code(self.crs)

    @staticmethod
    def bearing(from_coord: UTM, to_coord: UTM, as_deg: bool = True) -> float:
        """Calculate bearing from one UTM coordinate to another.

        Args:
            from_coord: Starting UTM coordinate
            to_coord: Ending UTM coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, π/2 = east, π = south, 3π/2 = west)
            Range is always [0, 360] degrees or [0, 2π] radians regardless of coordinate positions.

        Raises:
            ValueError: If coordinates are in different UTM zones
        """
        # Validate coordinates are in the same UTM zone
        if from_coord.crs != to_coord.crs:
            raise ValueError(f"Cannot calculate bearing between coordinates in different UTM zones: {from_coord.crs} vs {to_coord.crs}")

        # Calculate bearing in UTM coordinate system
        dx = to_coord.easting_m - from_coord.easting_m
        dy = to_coord.northing_m - from_coord.northing_m

        bearing = np.arctan2(dx, dy)  # Note: dx/easting, dy/northing for bearing

        # Normalize to [0, 2π] radians
        bearing = (bearing + 2 * np.pi) % (2 * np.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = np.degrees(bearing)

        return bearing

    @staticmethod
    def distance(coord1: UTM, coord2: UTM) -> float:
        """Calculate Euclidean distance between two UTM coordinates.

        Calculates the straight-line Euclidean distance between two points
        in the same UTM coordinate system.

        Args:
            coord1: First UTM coordinate
            coord2: Second UTM coordinate

        Returns:
            Distance in meters between the two coordinates.

        Raises:
            ValueError: If coordinates are in different UTM zones
        """
        # Validate coordinates are in the same UTM zone
        if coord1.crs != coord2.crs:
            raise ValueError(f"Cannot calculate distance between coordinates in different UTM zones: {coord1.crs} vs {coord2.crs}")

        # Calculate differences
        dx = coord2.easting_m - coord1.easting_m
        dy = coord2.northing_m - coord1.northing_m
        dz = (coord2.altitude_m or 0) - (coord1.altitude_m or 0)

        # Euclidean distance
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        return distance


__all__ = [
    'UTM',
]
