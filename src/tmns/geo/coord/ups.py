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
#    File:    ups.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
UPS (Universal Polar Stereographic) coordinate implementation.
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
class UPS:
    """Universal Polar Stereographic coordinate (easting, northing, elevation)."""
    easting_m: float
    northing_m: float
    altitude_m: float | None = None
    hemisphere: str = "N"  # "N" for North pole, "S" for South pole
    crs: str = "EPSG:32661"  # Default to UPS North

    @staticmethod
    def create(easting_m: float, northing_m: float, hemisphere: str = "N", alt_m: float | None = None) -> 'UPS':
        """Create a UPS coordinate."""
        crs = "EPSG:32661" if hemisphere.upper() == "N" else "EPSG:32761"
        return UPS(easting_m=easting_m, northing_m=northing_m, hemisphere=hemisphere.upper(), crs=crs, altitude_m=alt_m)

    def type(self) -> Coordinate_Type:
        """Get the coordinate type."""
        return Coordinate_Type.UPS

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
    def distance(coord1: UPS, coord2: UPS) -> float:
        """Calculate Euclidean distance between two UPS coordinates.

        Calculates the straight-line Euclidean distance between two points
        in the UPS coordinate system.

        Args:
            coord1: First UPS coordinate
            coord2: Second UPS coordinate

        Returns:
            Distance in meters between the two coordinates.

        Raises:
            ValueError: If coordinates are in different hemispheres
        """
        # Validate coordinates are in the same hemisphere
        if coord1.hemisphere != coord2.hemisphere:
            raise ValueError(f"Cannot calculate distance between coordinates in different hemispheres: {coord1.hemisphere} vs {coord2.hemisphere}")

        # Calculate differences
        dx = coord2.easting_m - coord1.easting_m
        dy = coord2.northing_m - coord1.northing_m
        dz = (coord2.altitude_m or 0) - (coord1.altitude_m or 0)

        # Euclidean distance
        distance = np.sqrt(dx**2 + dy**2 + dz**2)
        return distance

    @staticmethod
    def bearing(from_coord: UPS, to_coord: UPS, as_deg: bool = True) -> float:
        """Calculate bearing from one UPS coordinate to another.

        Args:
            from_coord: Starting UPS coordinate
            to_coord: Ending UPS coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, π/2 = east, π = south, 3π/2 = west)
            Range is always [0, 360] degrees or [0, 2π] radians regardless of coordinate positions.

        Raises:
            ValueError: If coordinates are in different hemispheres
        """
        # Validate coordinates are in the same hemisphere
        if from_coord.hemisphere != to_coord.hemisphere:
            raise ValueError(f"Cannot calculate bearing between coordinates in different hemispheres: {from_coord.hemisphere} vs {to_coord.hemisphere}")

        # Calculate bearing in UPS coordinate system
        dx = to_coord.easting_m - from_coord.easting_m
        dy = to_coord.northing_m - from_coord.northing_m

        bearing = np.arctan2(dx, dy)  # Note: dx/easting, dy/northing for bearing

        # Normalize to [0, 2π] radians
        bearing = (bearing + 2 * np.pi) % (2 * np.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = np.degrees(bearing)

        return bearing

    def __post_init__(self):
        """Validate UPS coordinate parameters."""
        if self.hemisphere not in ["N", "S"]:
            raise ValueError(f"Hemisphere must be 'N' or 'S', got {self.hemisphere}")

        # Validate CRS matches hemisphere
        expected_crs = "EPSG:32661" if self.hemisphere == "N" else "EPSG:32761"
        if self.crs != expected_crs:
            raise ValueError(f"CRS {self.crs} does not match hemisphere {self.hemisphere}, expected {expected_crs}")


__all__ = [
    'UPS',
]
