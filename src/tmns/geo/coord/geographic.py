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

Geographic coordinates represent positions on Earth's surface using latitude,
longitude, and optionally altitude. This is the most common coordinate system
for human-readable location data and is the basis for GPS positioning.

Coordinate System:
- Latitude: -90° to 90° (negative = south, positive = north)
- Longitude: -180° to 180° (negative = west, positive = east)
- Altitude: meters above/below sea level (optional)
- EPSG:4326 (WGS84 Geographic)

Example:
    # Create a geographic coordinate
    geo = Geographic.create(40.7128, -74.0060, 10.5)  # NYC

    # Calculate distance between coordinates
    distance = Geographic.distance(geo1, geo2)

    # Calculate bearing between coordinates
    bearing = Geographic.bearing(geo1, geo2, as_deg=True)
"""

# Python Standard Libraries
from __future__ import annotations

import math
from dataclasses import dataclass

# Third-Party Libraries
from tmns.geo.coord.crs import CRS

# Project Libraries
from tmns.geo.coord.types import Extent_Params, Type


@dataclass
class Geographic:
    """Geographic coordinate for latitude/longitude positioning.

    Geographic coordinates use the familiar latitude/longitude system to
    represent positions on Earth's surface. This is the standard coordinate
    system used by GPS and most mapping applications.

    Attributes:
        latitude_deg: Latitude in degrees (-90 to 90, negative = south)
        longitude_deg: Longitude in degrees (-180 to 180, negative = west)
        altitude_m: Altitude/elevation in meters above sea level (optional)
        crs: Coordinate reference system (defaults to WGS84: EPSG:4326)

    Note:
        - Latitude: 0° = equator, 90° = north pole, -90° = south pole
        - Longitude: 0° = prime meridian (Greenwich), 180° = international date line
        - Altitude: Positive = above sea level, Negative = below sea level
        - Uses WGS84 datum by default (EPSG:4326)
    """
    latitude_deg: float
    longitude_deg: float
    altitude_m: float | None = None
    crs: CRS = CRS.from_epsg(4326)  # Default to WGS84

    @staticmethod
    def create(lat_deg: float, lon_deg: float, alt_m: float | None = None) -> Geographic:
        """Create a geographic coordinate.

        Args:
            lat_deg: Latitude in degrees (-90 to 90)
            lon_deg: Longitude in degrees (-180 to 180)
            alt_m: Altitude/elevation in meters above sea level

        Returns:
            Geographic coordinate with specified components

        Raises:
            ValueError: If latitude or longitude is outside valid range

        Example:
            # New York City
            nyc = Geographic.create(40.7128, -74.0060, 10.5)

            # Sydney (no altitude)
            sydney = Geographic.create(-33.8688, 151.2093)
        """
        return Geographic(latitude_deg=lat_deg, longitude_deg=lon_deg, altitude_m=alt_m)

    def type(self) -> Type:
        """Get the coordinate type identifier.

        Returns:
            Type.GEOGRAPHIC indicating this is a latitude/longitude coordinate
        """
        return Type.GEOGRAPHIC

    def __post_init__(self):
        """Validate coordinate ranges and CRS."""
        # Validate coordinate bounds
        self._validate_bounds()

        # Validate CRS matches expected EPSG for geographic coordinates
        if self.crs.epsg_code != 4326:
            raise ValueError(f"CRS {self.crs} does not match geographic coordinates, expected EPSG:4326")

    def _validate_bounds(self) -> None:
        """
        Validate geographic coordinate bounds.

        Geographic coordinates must be within valid ranges:
        - Latitude: -90° to 90° degrees
        - Longitude: -180° to 180° degrees

        Raises:
            ValueError: If coordinates are outside valid ranges
        """
        if not -90 <= self.latitude_deg <= 90:
            raise ValueError(f"Latitude {self.latitude_deg} out of range [-90, 90]")
        if not -180 <= self.longitude_deg <= 180:
            raise ValueError(f"Longitude {self.longitude_deg} out of range [-180, 180]")

    def to_tuple(self) -> tuple[float, float]:
        """Convert to 2D coordinate tuple.

        Returns:
            Tuple of (longitude_deg, latitude_deg) in degrees
        """
        return (self.longitude_deg, self.latitude_deg)

    def to_3d_tuple(self) -> tuple[float, float, float]:
        """Convert to 3D coordinate tuple.

        Returns:
            Tuple of (longitude_deg, latitude_deg, altitude_m) where altitude defaults to 0.0 if None
        """
        return (self.longitude_deg, self.latitude_deg, self.altitude_m or 0.0)

    def to_leaflet(self) -> list[float]:
        """Convert to Leaflet/folium [lat, lon] list.

        Leaflet and folium use latitude-first ordering, which is the reverse
        of GeoJSON / ``to_tuple()``.  Use this whenever passing coordinates
        to a folium constructor or a JavaScript map call.

        Returns:
            ``[latitude_deg, longitude_deg]``
        """
        return [self.latitude_deg, self.longitude_deg]

    def copy(self) -> Geographic:
        """Create an independent copy of this geographic coordinate.

        Returns:
            New geographic coordinate with identical values but independent object
        """
        return Geographic(
            latitude_deg=self.latitude_deg,
            longitude_deg=self.longitude_deg,
            altitude_m=self.altitude_m,
            crs=self.crs
        )

    def __str__(self) -> str:
        """String representation."""
        if self.altitude_m is not None:
            return f"Geographic({self.latitude_deg:.6f}, {self.longitude_deg:.6f}, {self.altitude_m:.1f}m)"
        return f"Geographic({self.latitude_deg:.6f}, {self.longitude_deg:.6f})"

    def __hash__(self) -> int:
        """Generate hash value for geographic coordinate.

        Returns:
            Hash based on coordinate values and CRS
        """
        return hash((self.latitude_deg, self.longitude_deg, self.altitude_m, self.crs))

    def __eq__(self, other: object) -> bool:
        """Check equality with another geographic coordinate.

        Args:
            other: Object to compare against

        Returns:
            True if all coordinate components match exactly, False otherwise
        """
        if not isinstance(other, Geographic):
            return False
        return (self.latitude_deg == other.latitude_deg and
                self.longitude_deg == other.longitude_deg and
                self.altitude_m == other.altitude_m and
                self.crs == other.crs)

    def __add__(self, other: Geographic) -> Geographic:
        """Add two geographic coordinates (vector addition in degrees).

        Args:
            other: Another geographic coordinate to add

        Returns:
            New geographic coordinate representing the vector sum

        Raises:
            TypeError: If other is not a geographic coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, Geographic):
            raise TypeError("Can only add Geographic to Geographic")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot add geographic coordinates in different CRS: {self.crs} vs {other.crs}")

        return Geographic(
            latitude_deg=self.latitude_deg + other.latitude_deg,
            longitude_deg=self.longitude_deg + other.longitude_deg,
            altitude_m=(self.altitude_m if self.altitude_m is not None else 0) +
                       (other.altitude_m if other.altitude_m is not None else 0) or None,
            crs=self.crs
        )

    def __sub__(self, other: Geographic) -> Geographic:
        """Subtract two geographic coordinates (vector subtraction in degrees).

        Args:
            other: Another geographic coordinate to subtract

        Returns:
            New geographic coordinate representing the vector difference

        Raises:
            TypeError: If other is not a geographic coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, Geographic):
            raise TypeError("Can only subtract Geographic from Geographic")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot subtract geographic coordinates in different CRS: {self.crs} vs {other.crs}")

        return Geographic(
            latitude_deg=self.latitude_deg - other.latitude_deg,
            longitude_deg=self.longitude_deg - other.longitude_deg,
            altitude_m=(self.altitude_m if self.altitude_m is not None else 0) -
                       (other.altitude_m if other.altitude_m is not None else 0) or None,
            crs=self.crs
        )


    @staticmethod
    def bearing(from_coord: Geographic, to_coord: Geographic, as_deg: bool = True) -> float:
        """Calculate compass bearing from one geographic coordinate to another.

        Computes the initial bearing from point A to point B using the great
        circle navigation formula. The bearing is measured clockwise from
        true north.

        Args:
            from_coord: Starting geographic coordinate
            to_coord: Ending geographic coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Compass bearing measured clockwise from true north:
            - If as_deg=True: degrees in range [0, 360]
              (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians in range [0, 2π]
              (0 = north, π/2 = east, π = south, 3π/2 = west)

        Example:
            # North (same longitude, higher latitude)
            geo1 = Geographic.create(40.0, -74.0)
            geo2 = Geographic.create(41.0, -74.0)
            bearing = Geographic.bearing(geo1, geo2)  # Returns ~0.0 (north)

            # East (higher longitude, same latitude)
            geo3 = Geographic.create(40.0, -73.0)
            bearing = Geographic.bearing(geo1, geo3)  # Returns ~90.0 (east)
        """
        # Convert to radians
        lat1 = math.radians(from_coord.latitude_deg)
        lon1 = math.radians(from_coord.longitude_deg)
        lat2 = math.radians(to_coord.latitude_deg)
        lon2 = math.radians(to_coord.longitude_deg)

        # Calculate bearing
        dlon = lon2 - lon1

        y = math.sin(dlon) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) -
             math.sin(lat1) * math.cos(lat2) * math.cos(dlon))

        bearing = math.atan2(y, x)

        # Normalize to [0, 2π] radians
        bearing = (bearing + 2 * math.pi) % (2 * math.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = math.degrees(bearing)

        return bearing

    @staticmethod
    def distance(coord1: Geographic, coord2: Geographic) -> float:
        """Calculate great circle distance between two geographic coordinates.

        Uses the Haversine formula to calculate the great circle distance
        between two points on the Earth's surface. This accounts for the
        Earth's spherical geometry and provides accurate distances for
        most practical purposes.

        Args:
            coord1: First geographic coordinate
            coord2: Second geographic coordinate

        Returns:
            Distance in meters between the two coordinates

        Example:
            # Distance between New York and London
            nyc = Geographic.create(40.7128, -74.0060)
            london = Geographic.create(51.5074, -0.1278)
            distance = Geographic.distance(nyc, london)  # ~5,570,000 meters
        """
        # Earth's radius in meters (mean radius)
        R = 6371000.0

        # Convert to radians
        lat1 = math.radians(coord1.latitude_deg)
        lon1 = math.radians(coord1.longitude_deg)
        lat2 = math.radians(coord2.latitude_deg)
        lon2 = math.radians(coord2.longitude_deg)

        # Differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Haversine formula
        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

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

    @staticmethod
    def compute_extent_params(min_coord: Geographic, max_coord: Geographic, shape: tuple[int, int]) -> Extent_Params:
        """Compute extent parameters for grid generation.

        Args:
            min_coord: Minimum coordinate (southwest corner)
            max_coord: Maximum coordinate (northeast corner)
            shape: Output shape (width, height) in pixels

        Returns:
            Extent_Params with width_deg, height_deg, lon_step, lat_step
        """
        width_deg = max_coord.longitude_deg - min_coord.longitude_deg
        height_deg = max_coord.latitude_deg - min_coord.latitude_deg
        out_w, out_h = shape
        lon_step = width_deg / out_w
        lat_step = height_deg / out_h
        return Extent_Params( width  = width_deg,
                              height = height_deg,
                              step_x = lon_step,
                              step_y = lat_step )
