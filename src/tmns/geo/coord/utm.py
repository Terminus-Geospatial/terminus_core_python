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

Universal Transverse Mercator (UTM) is a projected coordinate system that divides
the Earth into 60 zones, each 6 degrees of longitude wide. UTM coordinates are
commonly used in surveying, mapping, and GIS applications because they provide
accurate distance and area calculations within each zone.

Each UTM zone has its own coordinate system with easting and northing values
in meters. The northern hemisphere uses zones 32601-32660, while the southern
hemisphere uses zones 32701-32760.
"""

# Python Standard Libraries
from __future__ import annotations

from dataclasses import dataclass

# Third-Party Libraries
import numpy as np

from tmns.geo.coord.crs import CRS

# Project Libraries
from tmns.geo.coord.types import Type


@dataclass
class UTM:
    """
    Universal Transverse Mercator coordinate (easting, northing, elevation).

    Represents a coordinate in the UTM projected coordinate system, which provides
    accurate distance and area calculations within 6-degree longitude zones.
    UTM coordinates are in meters and are widely used in surveying and GIS.

    Attributes:
        easting_m: Easting coordinate in meters (horizontal position within zone)
        northing_m: Northing coordinate in meters (vertical position within zone)
        altitude_m: Altitude/elevation in meters above sea level (optional)
        crs: Coordinate reference system object (should be UTM zone CRS)
    """
    easting_m: float
    northing_m: float
    altitude_m: float | None = None
    crs: CRS = None  # Should be set to appropriate UTM zone CRS

    def __post_init__(self):
        """Validate coordinates and set default CRS if not provided."""
        if self.crs is None:
            # Default to UTM zone 10N as a reasonable default
            self.crs = CRS.utm_zone(10, 'N')

        # Validate coordinate bounds
        self._validate_bounds()

    @staticmethod
    def create(easting_m: float, northing_m: float, crs: CRS = None, alt_m: float | None = None) -> UTM:
        """
        Create a UTM coordinate.

        Args:
            easting_m: Easting coordinate in meters
            northing_m: Northing coordinate in meters
            crs: Coordinate reference system object (should be UTM zone CRS)
            alt_m: Altitude in meters above sea level (optional)

        Returns:
            UTM coordinate instance
        """
        return UTM(easting_m=easting_m, northing_m=northing_m, crs=crs, altitude_m=alt_m)

    def type(self) -> Type:
        """
        Get the coordinate type.

        Returns:
            Type.UTM enum value
        """
        return Type.UTM

    def to_tuple(self) -> tuple[float, float]:
        """
        Convert to (easting, northing) tuple.

        Returns:
            Tuple containing (easting_m, northing_m)
        """
        return (self.easting_m, self.northing_m)

    def to_3d_tuple(self) -> tuple[float, float, float]:
        """
        Convert to (easting, northing, elevation) tuple.

        Returns:
            Tuple containing (easting_m, northing_m, altitude_m or 0.0)
        """
        return (self.easting_m, self.northing_m, self.altitude_m or 0.0)

    def copy(self) -> UTM:
        """
        Create a copy of this UTM coordinate.

        Returns:
            New UTM instance with identical values
        """
        return UTM(easting_m=self.easting_m, northing_m=self.northing_m,
                   altitude_m=self.altitude_m, crs=self.crs)

    def __hash__(self) -> int:
        """
        Make UTM hashable for use in sets and as dictionary keys.

        Returns:
            Hash value based on coordinate components
        """
        return hash((self.easting_m, self.northing_m, self.altitude_m, self.crs))

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another UTM coordinate.

        Args:
            other: Object to compare against

        Returns:
            True if coordinates are identical, False otherwise
        """
        if not isinstance(other, UTM):
            return False
        return (self.easting_m == other.easting_m and
                self.northing_m == other.northing_m and
                self.altitude_m == other.altitude_m and
                self.crs == other.crs)

    def __str__(self) -> str:
        """
        String representation of the coordinate.

        Returns:
            Human-readable string representation
        """
        alt_str = f", altitude={self.altitude_m:.2f}" if self.altitude_m is not None else ", altitude=None"
        return f"UTM(easting={self.easting_m:.2f}, northing={self.northing_m:.2f}, crs={self.crs}{alt_str})"

    def __add__(self, other: UTM) -> UTM:
        """
        Add two UTM coordinates (vector addition).

        Performs vector addition of coordinates, requiring both coordinates
        to be in the same UTM zone and coordinate reference system.

        Args:
            other: UTM coordinate to add

        Returns:
            New UTM coordinate representing the sum

        Raises:
            TypeError: If other is not a UTM coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, UTM):
            raise TypeError("Can only add UTM to UTM")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot add UTM coordinates in different CRS: {self.crs} vs {other.crs}")

        return UTM(easting_m=self.easting_m + other.easting_m,
                  northing_m=self.northing_m + other.northing_m,
                  altitude_m=self.altitude_m if self.altitude_m is not None else other.altitude_m,
                  crs=self.crs)

    def __sub__(self, other: UTM) -> UTM:
        """
        Subtract two UTM coordinates (vector subtraction).

        Performs vector subtraction of coordinates, requiring both coordinates
        to be in the same UTM zone and coordinate reference system.

        Args:
            other: UTM coordinate to subtract

        Returns:
            New UTM coordinate representing the difference

        Raises:
            TypeError: If other is not a UTM coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, UTM):
            raise TypeError("Can only subtract UTM from UTM")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot subtract UTM coordinates in different CRS: {self.crs} vs {other.crs}")

        return UTM(easting_m=self.easting_m - other.easting_m,
                  northing_m=self.northing_m - other.northing_m,
                  altitude_m=self.altitude_m if self.altitude_m is not None else other.altitude_m,
                  crs=self.crs)

    @property
    def crs_code(self) -> str:
        """
        Get the CRS code.

        Returns:
            CRS identifier string
        """
        return str(self.crs.epsg_code)

    @property
    def zone_number(self) -> int:
        """
        Extract zone number from CRS code.

        Parses the UTM zone number from the EPSG code. Northern hemisphere
        zones use EPSG:326xx, southern hemisphere zones use EPSG:327xx.

        Returns:
            UTM zone number (1-60)

        Raises:
            ValueError: If CRS code is not a valid UTM EPSG code
        """
        zone, _ = self.crs.get_utm_zone_info()
        return zone

    @property
    def hemisphere(self) -> str:
        """
        Extract hemisphere from CRS code.

        Determines whether the UTM coordinate is in the northern or southern
        hemisphere based on the EPSG code prefix.

        Returns:
            "N" for northern hemisphere, "S" for southern hemisphere

        Raises:
            ValueError: If CRS code is not a valid UTM EPSG code
        """
        _, hemisphere = self.crs.get_utm_zone_info()
        return hemisphere

    @property
    def central_meridian(self) -> float:
        """
        Calculate central meridian for the UTM zone.

        Each UTM zone is 6 degrees wide, with the central meridian at the
        center of the zone. Zone 1 starts at -180° longitude.

        Returns:
            Central meridian longitude in degrees
        """
        zone = self.zone_number
        return -183 + (zone * 6)  # Zone 1: -177°, Zone 10: -123°, Zone 60: 177°

    @staticmethod
    def bearing(from_coord: UTM, to_coord: UTM, as_deg: bool = True) -> float:
        """
        Calculate bearing from one UTM coordinate to another.

        Computes the compass bearing from a starting coordinate to an ending
        coordinate within the same UTM zone. The bearing is measured
        clockwise from true north in the UTM coordinate system.

        Args:
            from_coord: Starting UTM coordinate
            to_coord: Ending UTM coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, Ï/2 = east, Ï = south, 3Ï/2 = west)
            Range is always [0, 360] degrees or [0, 2Ï] radians regardless of coordinate positions.

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

        # Normalize to [0, 2Ï] radians
        bearing = (bearing + 2 * np.pi) % (2 * np.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = np.degrees(bearing)

        return bearing

    @staticmethod
    def distance(coord1: UTM, coord2: UTM) -> float:
        """
        Calculate Euclidean distance between two UTM coordinates.

        Computes the straight-line Euclidean distance between two points
        in the same UTM coordinate system, including elevation differences.

        Args:
            coord1: First UTM coordinate
            coord2: Second UTM coordinate

        Returns:
            Distance in meters between the two coordinates

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

    def _validate_bounds(self) -> None:
        """
        Validate UTM coordinate bounds.

        UTM coordinates have standard valid ranges:
        - Easting: 100,000 to 999,999 meters (with some overlap)
        - Northing: 0 to 10,000,000 meters

        Raises:
            ValueError: If coordinates are outside valid bounds
        """
        # Easting bounds (allowing some overlap between zones)
        if not (50000 <= self.easting_m <= 1000000):
            raise ValueError(f"UTM easting {self.easting_m} is outside valid range [50,000, 1,000,000] meters")

        # Northing bounds
        if not (0 <= self.northing_m <= 10000000):
            raise ValueError(f"UTM northing {self.northing_m} is outside valid range [0, 10,000,000] meters")
