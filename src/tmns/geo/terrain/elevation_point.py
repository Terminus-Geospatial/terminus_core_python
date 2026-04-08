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
#    File:    elevation_point.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Elevation point with coordinate and metadata.

This module provides the Elevation_Point class which represents an elevation
data point at a specific geographic location. Each elevation point includes
the coordinate with elevation value, source information, accuracy estimates,
and vertical datum support. The class supports conversion between different
coordinate systems and vertical datums, making it suitable for integration
with various elevation data sources and geospatial applications.

Key features:
- Coordinate system conversions (UTM, UPS, Web Mercator, ECEF)
- Vertical datum transformations (ellipsoidal, orthometric heights)
- Source tracking and accuracy metadata
- Factory methods for convenient creation
- Comprehensive string representations

Example:
    >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP")
    >>> print(point.elevation)  # 10.5 meters
    >>> utm_coord = point.to_utm()  # Convert to UTM
"""

# Python Standard Libraries
from dataclasses import dataclass, field

# Project Libraries
from tmns.geo.coord import Transformer, Geographic, Coordinate, Type, UTM, UPS, Web_Mercator, ECEF
from tmns.geo.coord.vdatum import Base as VBase


@dataclass
class Elevation_Point:
    """
    Elevation data point with coordinate and metadata.

    Represents an elevation measurement at a specific geographic location
    with comprehensive metadata for geospatial applications. Each point
    maintains its original coordinate system while supporting conversions
    to other coordinate systems and vertical datums.

    Attributes:
        coord: Geographic coordinate (latitude, longitude, elevation) in degrees
        source: Name of the elevation data source (e.g., "USGS 3DEP", "SRTM")
        accuracy: Estimated accuracy of elevation measurement in meters (None if unknown)
        vertical_datum: Vertical datum used for elevation (None if ellipsoidal)
        _transformer: Internal coordinate transformer for conversions (private)

    Note:
        The coordinate is always stored as Geographic to maintain consistency,
        but the class can convert to any supported coordinate system on demand.
        Vertical datum conversions preserve the original coordinate while
        adjusting the elevation value appropriately.
    """
    coord: Geographic
    source: str
    accuracy: float | None = None
    vertical_datum: VBase | None = None
    _transformer: Transformer = field(default_factory=Transformer, init=False)

    def __post_init__(self):
        """
        Validate coordinate type and initialize elevation point.

        Ensures that the provided coordinate is a Geographic coordinate,
        as this class requires geographic coordinates for internal storage
        and vertical datum conversions.

        Raises:
            TypeError: If coordinate is not a Geographic instance
        """
        if not isinstance(self.coord, Geographic):
            raise TypeError(f"Elevation_Point coord must be Geographic, got {type(self.coord)}")

    # ============================================================================
    # FACTORY METHODS
    # ============================================================================

    @classmethod
    def create(cls, latitude: float, longitude: float, elevation: float, source: str,
               accuracy: float | None = None, vertical_datum: VBase | None = None) -> Elevation_Point:
        """
        Create elevation point from individual geographic components.

        Factory method that creates an Elevation_Point from latitude, longitude,
        and elevation values. This is the preferred way to create elevation points
        when working with raw coordinate data.

        Args:
            latitude: Latitude in decimal degrees (-90 to 90)
            longitude: Longitude in decimal degrees (-180 to 180)
            elevation: Elevation height in meters above/below datum
            source: Name of the elevation data source (e.g., "USGS 3DEP", "SRTM")
            accuracy: Estimated accuracy in meters (None if unknown)
            vertical_datum: Vertical datum for elevation (None for ellipsoidal)

        Returns:
            Elevation_Point instance with geographic coordinate

        Example:
            >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP")
            >>> print(point.coord.latitude_deg)  # 40.7128
            >>> print(point.source)  # "USGS 3DEP"
        """
        coord = Geographic.create(latitude, longitude, elevation)
        return cls(coord, source, accuracy, vertical_datum)

    # ============================================================================
    # COORDINATE ACCESS METHODS
    # ============================================================================

    def coordinate(self) -> Geographic:
        """
        Get the underlying geographic coordinate.

        Returns the stored Geographic coordinate containing latitude, longitude,
        and elevation. This is the primary coordinate representation used
        internally by the Elevation_Point class.

        Returns:
            Geographic coordinate with elevation value

        Example:
            >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP")
            >>> coord = point.coordinate()
            >>> print(coord.latitude_deg)  # 40.7128
            >>> print(coord.altitude_m)   # 10.5
        """
        return self.coord

    # ============================================================================
    # COORDINATE CONVERSION METHODS
    # ============================================================================

    def to_utm(self) -> UTM:
        """
        Convert the elevation point to UTM coordinate.

        Transforms the stored geographic coordinate to Universal Transverse
        Mercator (UTM) projection while preserving the elevation value.
        The resulting UTM coordinate includes the same elevation as the
        original geographic coordinate.

        Returns:
            UTM coordinate with easting, northing, zone, and elevation

        Example:
            >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP")
            >>> utm = point.to_utm()
            >>> print(utm.zone_number)  # UTM zone number
            >>> print(utm.easting)     # Easting in meters
        """
        return self._transformer.geo_to_utm(self.coord)

    def to_ups(self) -> UPS:
        """
        Convert the elevation point to UPS coordinate.

        Transforms the stored geographic coordinate to Universal Polar Stereographic
        (UPS) projection while preserving the elevation value. UPS is primarily
        used for polar regions (above 84°N and below 80°S).

        Returns:
            UPS coordinate with easting, northing, hemisphere, and elevation
        """
        return self._transformer.geo_to_ups(self.coord)

    def to_web_mercator(self) -> Web_Mercator:
        """
        Convert the elevation point to Web Mercator coordinate.

        Transforms the stored geographic coordinate to Web Mercator projection
        (EPSG:3857) while preserving the elevation value. This is the coordinate
        system used by most web mapping applications.

        Returns:
            Web Mercator coordinate with x, y, and elevation
        """
        return self._transformer.geo_to_web_mercator(self.coord)

    def to_ecef(self) -> ECEF:
        """
        Convert the elevation point to ECEF coordinate.

        Transforms the stored geographic coordinate to Earth-Centered, Earth-Fixed
        (ECEF) Cartesian coordinate system while preserving the elevation value.
        ECEF coordinates are useful for 3D calculations and satellite-based
        applications.

        Returns:
            ECEF coordinate with x, y, z components in meters
        """
        return self._transformer.geo_to_ecef(self.coord)

    # ============================================================================
    # VERTICAL DATUM CONVERSION METHODS
    # ============================================================================

    def to_vertical_datum(self, target_datum: VBase) -> Elevation_Point:
        """
        Convert elevation to different vertical datum.

        Performs vertical datum transformation by converting the current elevation
        to ellipsoidal height (if needed), then transforming to the target datum.
        This method preserves the geographic coordinate while adjusting only the
        elevation value to match the new vertical datum.

        Args:
            target_datum: Target vertical datum for conversion (e.g., EGM96, NAVD88)

        Returns:
            New Elevation_Point with elevation in target vertical datum

        Raises:
            ValueError: If datum transformation fails due to invalid coordinates
                        or unsupported datum transformations

        Example:
            >>> from tmns.geo.coord.vdatum import EGM96, NAVD88
            >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP", vertical_datum=EGM96)
            >>> navd_point = point.to_vertical_datum(NAVD88)
            >>> print(navd_point.coord.altitude_m)  # Different elevation value
            >>> print(navd_point.vertical_datum.name)  # "NAVD88"
        """
        if self.vertical_datum == target_datum:
            return self

        # Use coordinate-based API for cleaner conversion
        try:
            # Convert to ellipsoidal first (if not already)
            if self.vertical_datum:
                ellip_coord = self.vertical_datum.to_ellipsoidal(self.coord)
            else:
                ellip_coord = self.coord  # Already ellipsoidal

            # Convert based on target datum type
            if target_datum.name == "Ellipsoidal":
                # Target wants ellipsoidal height
                target_coord = ellip_coord
            else:
                # Target wants orthometric height
                target_coord = target_datum.to_orthometric(ellip_coord)

            return Elevation_Point(
                coord=target_coord,
                source=self.source,
                accuracy=self.accuracy,
                vertical_datum=target_datum
            )
        except Exception as e:
            raise ValueError(f"Failed to convert to datum {target_datum}: {e}")

    # ============================================================================
    # COMPARISON AND STRING METHODS
    # ============================================================================

    def __str__(self) -> str:
        """
        Human-readable string representation of the elevation point.

        Returns a formatted string showing the elevation value, geographic location,
        vertical datum (if specified), and data source. This is suitable for
        display in user interfaces and logging.

        Returns:
            Formatted string: "Elevation: X.Xm at lat,lon [datum] [source]"

        Example:
            >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP")
            >>> print(point)
            "Elevation: 10.5m at 40.7128, -74.0060 [USGS 3DEP]"
        """
        datum_str = f" [{self.vertical_datum.name}]" if self.vertical_datum else ""
        return f"Elevation: {self.coord.altitude_m or 0.0:.1f}m at {self.coord}{datum_str} [{self.source}]"

    def __repr__(self) -> str:
        """
        Detailed string representation for debugging and development.

        Returns a comprehensive string representation that includes all attributes
        of the elevation point. This is useful for debugging, logging, and
        development purposes where the complete object state is needed.

        Returns:
            Detailed string with all object attributes

        Example:
            >>> point = Elevation_Point.create(40.7128, -74.0060, 10.5, "USGS 3DEP")
            >>> repr(point)
            "Elevation_Point(coord=Geographic(...), source='USGS 3DEP', accuracy=None, vertical_datum=None)"
        """
        return f"Elevation_Point(coord={self.coord!r}, source={self.source!r}, accuracy={self.accuracy!r}, vertical_datum={self.vertical_datum!r})"
