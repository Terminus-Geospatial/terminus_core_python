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
#    File:    geographic.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Geographic coordinate implementation.
"""

# Python Standard Libraries
import math
from dataclasses import dataclass
from typing import Union

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type
from tmns.geo.coord.epsg import EPSG_Manager


@dataclass
class Geographic:
    """Geographic coordinate (latitude, longitude, elevation)."""
    latitude_deg: float
    longitude_deg: float
    altitude_m: float | None = None

    @staticmethod
    def create(lat_deg: float, lon_deg: float, alt_m: float | None = None) -> 'Geographic':
        """Create a geographic coordinate."""
        return Geographic(latitude_deg=lat_deg, longitude_deg=lon_deg, altitude_m=alt_m)

    def type(self) -> Coordinate_Type:
        """Get the coordinate type."""
        return Coordinate_Type.GEOGRAPHIC

    def __post_init__(self):
        """Validate coordinate ranges."""
        if not -90 <= self.latitude_deg <= 90:
            raise ValueError(f"Latitude {self.latitude_deg} out of range [-90, 90]")
        if not -180 <= self.longitude_deg <= 180:
            raise ValueError(f"Longitude {self.longitude_deg} out of range [-180, 180]")

    def to_tuple(self) -> tuple[float, float]:
        """Convert to (lon, lat) tuple."""
        return (self.longitude_deg, self.latitude_deg)

    def to_3d_tuple(self) -> tuple[float, float, float]:
        """Convert to (lon, lat, elevation) tuple."""
        return (self.longitude_deg, self.latitude_deg, self.altitude_m or 0.0)

    def __str__(self) -> str:
        """String representation."""
        if self.altitude_m is not None:
            return f"({self.latitude_deg:.6f}, {self.longitude_deg:.6f}, {self.altitude_m:.1f}m)"
        return f"({self.latitude_deg:.6f}, {self.longitude_deg:.6f})"

    def to_epsg(self) -> int:
        """Get EPSG code for this coordinate."""
        return EPSG_Manager.WGS84

    @staticmethod
    def bearing(from_coord: Geographic, to_coord: Geographic, as_deg: bool = True) -> float:
        """Calculate bearing from one geographic coordinate to another.

        Args:
            from_coord: Starting geographic coordinate
            to_coord: Ending geographic coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, π/2 = east, π = south, 3π/2 = west)
            Range is always [0, 360] degrees or [0, 2π] radians regardless of coordinate positions.
        """
        # Convert to radians
        lat1 = from_coord.lat_rad
        lon1 = from_coord.lon_rad
        lat2 = to_coord.lat_rad
        lon2 = to_coord.lon_rad

        # Calculate bearing
        dlon = lon2 - lon1

        y = np.sin(dlon) * np.cos(lat2)
        x = (np.cos(lat1) * np.sin(lat2) -
             np.sin(lat1) * np.cos(lat2) * np.cos(dlon))

        bearing = np.arctan2(y, x)

        # Normalize to [0, 2π] radians
        bearing = (bearing + 2 * np.pi) % (2 * np.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = np.degrees(bearing)

        return bearing

    @staticmethod
    def distance(coord1: Geographic, coord2: Geographic) -> float:
        """Calculate great circle distance between two geographic coordinates.

        Uses the Haversine formula to calculate the great circle distance
        between two points on the Earth's surface.

        Args:
            coord1: First geographic coordinate
            coord2: Second geographic coordinate

        Returns:
            Distance in meters between the two coordinates.
        """
        # Earth's radius in meters (mean radius)
        R = 6371000.0

        # Convert to radians
        lat1 = coord1.lat_rad
        lon1 = coord1.lon_rad
        lat2 = coord2.lat_rad
        lon2 = coord2.lon_rad

        # Differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = (np.sin(dlat/2)**2 +
             np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2)
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))

        distance = R * c
        return distance

    @property
    def lat_deg(self) -> float:
        """Get latitude in degrees (backward compatibility)."""
        return self.latitude_deg

    @property
    def lat_rad(self) -> float:
        """Get latitude in radians."""
        return math.radians(self.latitude_deg)

    @property
    def lon_deg(self) -> float:
        """Get longitude in degrees (backward compatibility)."""
        return self.longitude_deg

    @property
    def lon_rad(self) -> float:
        """Get longitude in radians."""
        return math.radians(self.longitude_deg)

    @property
    def elevation(self) -> float | None:
        """Get elevation in meters."""
        return self.altitude_m


__all__ = [
    'Geographic',
]
