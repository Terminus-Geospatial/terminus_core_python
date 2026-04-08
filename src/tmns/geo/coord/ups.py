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

The Universal Polar Stereographic projection is a conformal map projection
used for mapping polar regions. UPS coordinates are defined for areas
north of 84°N and south of 80°S latitude.

Coordinate System:
- Easting: 0 to 4,000,000 meters from the pole
- Northing: 0 to 4,000,000 meters from the pole
- EPSG:32661 for North pole, EPSG:32761 for South pole

Example:
    # Create a UPS coordinate at the North pole center
    ups = UPS.create(2000000, 2000000, "N", 1000)

    # Calculate distance between two UPS coordinates
    distance = UPS.distance(ups1, ups2)

    # Calculate bearing between coordinates
    bearing = UPS.bearing(ups1, ups2, as_deg=True)
"""

# Python Standard Libraries
from __future__ import annotations

import math
from collections import namedtuple
from dataclasses import dataclass

# Third-Party Libraries
import numpy as np

from tmns.geo.coord.crs import CRS

# Project Libraries
from tmns.geo.coord.types import Type

# Define bounds as namedtuple for lightweight structure
UPS_Bounds = namedtuple('UPS_Bounds', ['min_easting', 'min_northing', 'max_easting', 'max_northing'])


@dataclass
class UPS:
    """Universal Polar Stereographic coordinate for polar regions.

    UPS coordinates are used for mapping areas near the poles where
    standard UTM projections become distorted. The projection uses
    a stereographic projection centered on the pole.

    Attributes:
        easting_m: Easting coordinate in meters (0 to 4,000,000)
        northing_m: Northing coordinate in meters (0 to 4,000,000)
        altitude_m: Altitude/elevation in meters above sea level
        hemisphere: "N" for North pole (84°N+), "S" for South pole (80°S+)
        crs: Coordinate reference system (EPSG:32661 for North, EPSG:32761 for South)

    Note:
        - Easting and Northing are measured from the pole
        - (2000000, 2000000) represents the pole center
        - Valid range: 0 ≤ easting, northing ≤ 4,000,000 meters
    """
    easting_m: float
    northing_m: float
    altitude_m: float | None = None
    hemisphere: str = "N"  # "N" for North pole, "S" for South pole
    crs: CRS = CRS.from_epsg(32661)  # Default to UPS North

    @staticmethod
    def create(easting_m: float, northing_m: float, hemisphere: str = "N", alt_m: float | None = None) -> UPS:
        """Create a UPS coordinate with proper CRS assignment.

        Args:
            easting_m: Easting coordinate in meters (0 to 4,000,000)
            northing_m: Northing coordinate in meters (0 to 4,000,000)
            hemisphere: "N" for North pole or "S" for South pole
            alt_m: Altitude/elevation in meters above sea level

        Returns:
            UPS coordinate with appropriate CRS based on hemisphere

        Raises:
            ValueError: If coordinates are outside valid bounds or hemisphere is invalid

        Example:
            # North pole center with altitude
            ups_north = UPS.create(2000000, 2000000, "N", 1000)

            # South pole coordinate without altitude
            ups_south = UPS.create(1500000, 2500000, "S")
        """
        crs = CRS.from_epsg(32661) if hemisphere.upper() == "N" else CRS.from_epsg(32761)
        return UPS(easting_m=easting_m, northing_m=northing_m, hemisphere=hemisphere.upper(), crs=crs, altitude_m=alt_m)

    @staticmethod
    def _create_without_validation(easting_m: float, northing_m: float, hemisphere: str, crs: CRS, alt_m: float | None = None) -> UPS:
        """Create a UPS coordinate without bounds validation.

        This is used internally for cases where we need to create coordinates
        that might be outside the normal UPS bounds (e.g., center offsets).

        Args:
            easting_m: Easting coordinate in meters
            northing_m: Northing coordinate in meters
            hemisphere: "N" for North pole or "S" for South pole
            crs: Coordinate reference system
            alt_m: Altitude/elevation in meters above sea level

        Returns:
            UPS coordinate without bounds validation
        """
        # Create UPS object directly, bypassing __post_init__ validation
        ups = object.__new__(UPS)
        ups.easting_m = easting_m
        ups.northing_m = northing_m
        ups.altitude_m = alt_m
        ups.hemisphere = hemisphere.upper()
        ups.crs = crs
        return ups

    def type(self) -> Type:
        """Get the coordinate type identifier.

        Returns:
            Type.UPS indicating this is a Universal Polar Stereographic coordinate
        """
        return Type.UPS

    def to_tuple(self) -> tuple[float, float]:
        """Convert to 2D coordinate tuple.

        Returns:
            Tuple of (easting_m, northing_m) in meters
        """
        return (self.easting_m, self.northing_m)

    def to_3d_tuple(self) -> tuple[float, float, float]:
        """Convert to 3D coordinate tuple.

        Returns:
            Tuple of (easting_m, northing_m, altitude_m) where altitude defaults to 0.0 if None
        """
        return (self.easting_m, self.northing_m, self.altitude_m or 0.0)


    def copy(self) -> UPS:
        """Create an independent copy of this UPS coordinate.

        Returns:
            New UPS coordinate with identical values but independent object
        """
        return UPS(easting_m=self.easting_m, northing_m=self.northing_m,
                   altitude_m=self.altitude_m, hemisphere=self.hemisphere, crs=self.crs)

    def __hash__(self) -> int:
        """Generate hash value for UPS coordinate.

        Returns:
            Hash based on all coordinate components including CRS
        """
        return hash((self.easting_m, self.northing_m, self.altitude_m, self.hemisphere, self.crs))

    def __eq__(self, other: object) -> bool:
        """Check equality with another UPS coordinate.

        Args:
            other: Object to compare against

        Returns:
            True if all coordinate components match exactly, False otherwise
        """
        if not isinstance(other, UPS):
            return False
        return (self.easting_m == other.easting_m and
                self.northing_m == other.northing_m and
                self.altitude_m == other.altitude_m and
                self.hemisphere == other.hemisphere and
                self.crs == other.crs)

    def __str__(self) -> str:
        """String representation."""
        alt_str = f", altitude={self.altitude_m:.2f}" if self.altitude_m is not None else ", altitude=None"
        return f"UPS(easting={self.easting_m:.2f}, northing={self.northing_m:.2f}, hemisphere={self.hemisphere}{alt_str})"

    def __add__(self, other: UPS) -> UPS:
        """Add two UPS coordinates (vector addition).

        Performs vector addition of UPS coordinates. Both coordinates must be
        in the same hemisphere/CRS. The result maintains the first coordinate's
        hemisphere and CRS.

        Args:
            other: Another UPS coordinate to add

        Returns:
            New UPS coordinate representing the vector sum

        Raises:
            TypeError: If other is not a UPS coordinate
            ValueError: If coordinates are in different CRS/hemispheres
        """
        if not isinstance(other, UPS):
            raise TypeError("Can only add UPS to UPS")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot add UPS coordinates in different CRS: {self.crs} vs {other.crs}")

        return UPS(easting_m=self.easting_m + other.easting_m,
                  northing_m=self.northing_m + other.northing_m,
                  altitude_m=self.altitude_m if self.altitude_m is not None else other.altitude_m,
                  hemisphere=self.hemisphere)

    def __sub__(self, other: UPS) -> UPS:
        """Subtract two UPS coordinates (vector subtraction).

        Performs vector subtraction of UPS coordinates. Both coordinates must be
        in the same hemisphere/CRS. The result maintains the first coordinate's
        hemisphere and CRS.

        Args:
            other: Another UPS coordinate to subtract

        Returns:
            New UPS coordinate representing the vector difference

        Raises:
            TypeError: If other is not a UPS coordinate
            ValueError: If coordinates are in different CRS/hemispheres
        """
        if not isinstance(other, UPS):
            raise TypeError("Can only subtract UPS from UPS")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot subtract UPS coordinates in different CRS: {self.crs} vs {other.crs}")

        return UPS(easting_m=self.easting_m - other.easting_m,
                  northing_m=self.northing_m - other.northing_m,
                  altitude_m=self.altitude_m if self.altitude_m is not None else other.altitude_m,
                  hemisphere=self.hemisphere)

    def is_in_bounds(self) -> bool:
        """Check if coordinate is within valid UPS bounds.

        Returns:
            True if both easting and northing are within [0, 4,000,000] meters
        """
        # UPS bounds: 0 to 4000000 for both easting and northing
        return (0 <= self.easting_m <= 4000000 and
                0 <= self.northing_m <= 4000000)

    def center_offset(self) -> UPS:
        """Calculate offset from UPS pole center.

        The UPS coordinate system is centered at (2000000, 2000000) which
        represents the pole. This method returns the offset from that center.

        Returns:
            New UPS coordinate representing offset from pole center

        Example:
            # Center coordinate (at pole)
            ups_center = UPS.create(2000000, 2000000, "N")
            offset = ups_center.center_offset()  # Returns (0, 0)

            # 100km east of center
            ups_east = UPS.create(2100000, 2000000, "N")
            offset = ups_east.center_offset()  # Returns (100000, 0)
        """
        # Create offset coordinate without bounds validation
        # since offsets can be negative (outside valid UPS range)
        return UPS._create_without_validation(
            easting_m=self.easting_m - 2000000.0,
            northing_m=self.northing_m - 2000000.0,
            hemisphere=self.hemisphere,
            crs=self.crs,
            alt_m=self.altitude_m
        )

    @staticmethod
    def bounds() -> UPS_Bounds:
        """Get the valid coordinate bounds for UPS.

        Returns:
            UPS_Bounds namedtuple with min/max values for easting and northing

        Example:
            bounds = UPS.bounds()
            print(f"Easting range: {bounds.min_easting} to {bounds.max_easting}")
            print(f"Northing range: {bounds.min_northing} to {bounds.max_northing}")
        """
        return UPS_Bounds(0, 0, 4000000, 4000000)

    @staticmethod
    def distance(coord1: UPS, coord2: UPS) -> float:
        """Calculate Euclidean distance between two UPS coordinates.

        Computes the straight-line distance between two points in the UPS
        coordinate system, including altitude differences if present.

        Args:
            coord1: First UPS coordinate
            coord2: Second UPS coordinate

        Returns:
            Distance in meters between the two coordinates

        Raises:
            TypeError: If either coordinate is not a UPS instance
            ValueError: If coordinates are in different hemispheres

        Example:
            ups1 = UPS.create(2000000, 2000000, "N", 0)
            ups2 = UPS.create(2100000, 2000000, "N", 100)
            distance = UPS.distance(ups1, ups2)  # ~100,000.5 meters
        """
        if not isinstance(coord1, UPS) or not isinstance(coord2, UPS):
            raise TypeError("Can only calculate distance between UPS coordinates")

        # Validate coordinates are in the same hemisphere
        if coord1.hemisphere != coord2.hemisphere:
            raise ValueError(f"Cannot calculate distance between coordinates in different hemispheres: {coord1.hemisphere} vs {coord2.hemisphere}")

        dx = coord1.easting_m - coord2.easting_m
        dy = coord1.northing_m - coord2.northing_m
        dz = (coord1.altitude_m or 0) - (coord2.altitude_m or 0)
        return math.sqrt(dx*dx + dy*dy + dz*dz)

    @staticmethod
    def bearing(from_coord: UPS, to_coord: UPS, as_deg: bool = True) -> float:
        """Calculate compass bearing from one UPS coordinate to another.

        Computes the azimuth bearing from a starting point to an ending point
        in the UPS coordinate system. The bearing is measured clockwise from
        true north (positive northing direction).

        Args:
            from_coord: Starting UPS coordinate
            to_coord: Ending UPS coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Compass bearing measured clockwise from true north:
            - If as_deg=True: degrees in range [0, 360]
              (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians in range [0, 2π]
              (0 = north, π/2 = east, π = south, 3π/2 = west)

        Raises:
            ValueError: If coordinates are in different hemispheres

        Example:
            # North (same easting, higher northing)
            ups1 = UPS.create(2000000, 2000000, "N")
            ups2 = UPS.create(2000000, 2100000, "N")
            bearing = UPS.bearing(ups1, ups2)  # Returns 0.0 (north)

            # East (higher easting, same northing)
            ups3 = UPS.create(2100000, 2000000, "N")
            bearing = UPS.bearing(ups1, ups3)  # Returns 90.0 (east)
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
        expected_epsg = 32661 if self.hemisphere == "N" else 32761
        if self.crs.epsg_code != expected_epsg:
            raise ValueError(f"CRS {self.crs} does not match hemisphere {self.hemisphere}, expected EPSG:{expected_epsg}")

        # Validate coordinate bounds
        self._validate_bounds()

    def _validate_bounds(self) -> None:
        """
        Validate UPS coordinate bounds during object creation.

        UPS coordinates must be within the valid range for the polar
        stereographic projection. This validation is automatically called
        during object initialization.

        Valid ranges:
        - Easting: 0 to 4,000,000 meters (measured from pole)
        - Northing: 0 to 4,000,000 meters (measured from pole)

        Coordinate system origin:
        - (0, 0) represents southwest corner of projection
        - (2000000, 2000000) represents the pole center
        - (4000000, 4000000) represents northeast corner

        Raises:
            ValueError: If easting or northing is outside valid range
        """
        # Easting bounds
        if not (0 <= self.easting_m <= 4000000):
            raise ValueError(f"UPS easting {self.easting_m} is outside valid range [0, 4,000,000] meters")

        # Northing bounds
        if not (0 <= self.northing_m <= 4000000):
            raise ValueError(f"UPS northing {self.northing_m} is outside valid range [0, 4,000,000] meters")
