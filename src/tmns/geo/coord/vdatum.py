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
#    File:    vdatum.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Vertical datum definitions and utilities.

This module contains vertical reference system definitions used for
converting between orthometric and ellipsoidal heights.
"""

# Python Standard Libraries
import logging
from dataclasses import dataclass

# Third-Party Libraries
import pyproj

# Project Libraries
from tmns.geo.coord.geographic import Geographic


@dataclass
class Base:
    """
    Base class for vertical reference systems.

    A vertical datum provides a reference surface for measuring heights.
    Common vertical datums include orthometric datums (referenced to mean sea level)
    and ellipsoidal datums (referenced to an ellipsoid surface).

    Attributes:
        name: Human-readable name of the vertical datum
        epsg_code: EPSG code for this datum (if available)
    """
    name: str
    epsg_code: int | None = None

    def separation_meters(self, coord: Geographic) -> float:
        """
        Get geoid separation (N) at the specified location.

        The geoid separation is the height difference between the reference ellipsoid
        and the geoid surface at the specified location.

        Args:
            coord: Geographic coordinate (latitude, longitude, altitude ignored)

        Returns:
            Geoid separation in meters (positive when geoid is above ellipsoid)

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"separation_meters not implemented for {self.name}")

    def to_ellipsoidal(self, coord: Geographic) -> Geographic:
        """
        Convert coordinate with orthometric height to ellipsoidal height.

        Orthometric height (H) is measured relative to the geoid.
        Ellipsoidal height (h) is measured relative to the reference ellipsoid.
        The relationship is: h = H + N, where N is the geoid separation.

        Args:
            coord: Geographic coordinate with orthometric height

        Returns:
            Geographic coordinate with ellipsoidal height

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"to_ellipsoidal not implemented for {self.name}")

    def to_orthometric(self, coord: Geographic) -> Geographic:
        """
        Convert coordinate with ellipsoidal height to orthometric height.

        The relationship is: H = h - N, where N is the geoid separation.

        Args:
            coord: Geographic coordinate with ellipsoidal height

        Returns:
            Geographic coordinate with orthometric height

        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError(f"to_orthometric not implemented for {self.name}")


class EGM96(Base):
    """
    Earth Gravitational Model 1996 vertical datum.

    EGM96 is a global geoid model providing geoid separations relative to WGS84.
    It provides approximately 0.5-1.0 meter accuracy globally.

    EPSG code: 5773

    This implementation uses pyproj for geoid transformations, which provides
    built-in support for EGM96 and other vertical datums.
    """

    def __init__(self):
        """Initialize EGM96 vertical datum using pyproj."""
        super().__init__("EGM96", epsg_code=5773)
        self.logger = logging.getLogger(__name__)

        # Create transformer for EGM96 geoid conversions
        # Use PROJ strings for more explicit vertical transformation
        self._transformer_to_egm96 = pyproj.Transformer.from_crs(
            "EPSG:4326+5773",  # WGS84 + EGM96 height
            "EPSG:4326",        # WGS84 ellipsoidal height
            always_xy=True
        )
        # Create transformer for reverse conversion
        self._transformer_from_egm96 = pyproj.Transformer.from_crs(
            "EPSG:4326",        # WGS84 ellipsoidal height
            "EPSG:4326+5773",  # WGS84 + EGM96 height
            always_xy=True
        )
        self.logger.info("EGM96: Using pyproj for geoid transformations")

    def separation_meters(self, coord: Geographic) -> float:
        """
        Get geoid separation (N) at the specified location using pyproj.

        Args:
            coord: Geographic coordinate (latitude, longitude, altitude ignored)

        Returns:
            Geoid separation in meters

        Raises:
            ValueError: If coordinates are out of range
        """
        # Validate coordinates
        if not (-90.0 <= coord.latitude_deg <= 90.0):
            raise ValueError(f"Latitude out of range: {coord.latitude_deg}. Must be -90 to 90 degrees.")

        if not (-180.0 <= coord.longitude_deg <= 180.0):
            raise ValueError(f"Longitude out of range: {coord.longitude_deg}. Must be -180 to 180 degrees.")

        try:
            # Use pyproj to get geoid separation
            # For a point at 0 elevation, the transformed height gives us the geoid separation
            x, y, z = self._transformer_to_egm96.transform(coord.longitude_deg, coord.latitude_deg, 0)
            return float(z)  # This is the geoid separation
        except Exception as e:
            self.logger.error(f"Error computing EGM96 geoid separation: {e}")
            raise

    def to_ellipsoidal(self, coord: Geographic) -> Geographic:
        """
        Convert orthometric height to ellipsoidal height using pyproj.

        Args:
            coord: Geographic coordinate with orthometric height

        Returns:
            Geographic coordinate with ellipsoidal height
        """
        if coord.altitude_m is None:
            raise ValueError("Coordinate must have altitude for conversion")

        try:
            # Use separation_meters to get geoid separation, then add to orthometric height
            geoid_separation = self.separation_meters(coord)
            ellipsoidal_height = coord.altitude_m + geoid_separation
            return Geographic(coord.latitude_deg, coord.longitude_deg, ellipsoidal_height)
        except Exception as e:
            self.logger.error(f"Error converting to ellipsoidal height: {e}")
            raise

    def to_orthometric(self, coord: Geographic) -> Geographic:
        """
        Convert ellipsoidal height to orthometric height using pyproj.

        Args:
            coord: Geographic coordinate with ellipsoidal height

        Returns:
            Geographic coordinate with orthometric height
        """
        if coord.altitude_m is None:
            raise ValueError("Coordinate must have altitude for conversion")

        try:
            # Use pyproj to convert from ellipsoidal to orthometric
            x, y, z = self._transformer_from_egm96.transform(coord.longitude_deg, coord.latitude_deg, coord.altitude_m)
            return Geographic(coord.latitude_deg, coord.longitude_deg, float(z))
        except Exception as e:
            self.logger.error(f"Error in ellipsoidal to orthometric conversion: {e}")
            raise


class NAVD88(Base):
    """
    North American Vertical Datum of 1988.

    NAVD88 is the vertical reference system used throughout North America.
    It provides orthometric heights relative to a fixed reference surface
    (approximately mean sea level at the tide gauge at Rimouski, Quebec).

    EPSG code: 5703

    NAVD88 is a static datum and does not account for post-glacial rebound
    or other vertical crustal movements. For high-precision applications,
    regional geoid models like GEOID12B should be used.

    This implementation uses pyproj for vertical datum transformations.
    """

    def __init__(self):
        """Initialize NAVD88 vertical datum using pyproj."""
        super().__init__("NAVD88", epsg_code=5703)
        self.logger = logging.getLogger(__name__)

        # Create transformer for NAVD88 conversions
        # Use PROJ strings for more explicit vertical transformation
        self._transformer_to_navd88 = pyproj.Transformer.from_crs(
            "EPSG:4326+5703",  # WGS84 + NAVD88 height
            "EPSG:4326",        # WGS84 ellipsoidal height
            always_xy=True
        )
        # Create transformer for reverse conversion
        self._transformer_from_navd88 = pyproj.Transformer.from_crs(
            "EPSG:4326",        # WGS84 ellipsoidal height
            "EPSG:4326+5703",  # WGS84 + NAVD88 height
            always_xy=True
        )
        self.logger.info("NAVD88: Using pyproj for vertical datum transformations")

    def separation_meters(self, coord: Geographic) -> float:
        """
        Get geoid separation (N) at the specified location using pyproj.

        Args:
            coord: Geographic coordinate (latitude, longitude, altitude ignored)

        Returns:
            Geoid separation in meters

        Raises:
            ValueError: If coordinates are out of range
        """
        # Validate coordinates
        if not (-90.0 <= coord.latitude_deg <= 90.0):
            raise ValueError(f"Latitude out of range: {coord.latitude_deg}. Must be -90 to 90 degrees.")

        if not (-180.0 <= coord.longitude_deg <= 180.0):
            raise ValueError(f"Longitude out of range: {coord.longitude_deg}. Must be -180 to 180 degrees.")

        try:
            # Use pyproj to get geoid separation
            # For a point at 0 elevation, the transformed height gives us the geoid separation
            x, y, z = self._transformer_to_navd88.transform(coord.longitude_deg, coord.latitude_deg, 0)
            return float(z)  # This is the geoid separation
        except Exception as e:
            self.logger.error(f"Error computing NAVD88 geoid separation: {e}")
            raise

    def to_ellipsoidal(self, coord: Geographic) -> Geographic:
        """
        Convert orthometric height to ellipsoidal height using pyproj.

        Args:
            coord: Geographic coordinate with orthometric height

        Returns:
            Geographic coordinate with ellipsoidal height
        """
        if coord.altitude_m is None:
            raise ValueError("Coordinate must have altitude for conversion")

        try:
            # Use pyproj to convert from orthometric to ellipsoidal
            x, y, z = self._transformer_to_navd88.transform(coord.longitude_deg, coord.latitude_deg, coord.altitude_m)
            return Geographic(coord.latitude_deg, coord.longitude_deg, float(z))
        except Exception as e:
            self.logger.error(f"Error in orthometric to ellipsoidal conversion: {e}")
            raise

    def to_orthometric(self, coord: Geographic) -> Geographic:
        """
        Convert ellipsoidal height to orthometric height using pyproj.

        Args:
            coord: Geographic coordinate with ellipsoidal height

        Returns:
            Geographic coordinate with orthometric height
        """
        if coord.altitude_m is None:
            raise ValueError("Coordinate must have altitude for conversion")

        try:
            # Use pyproj to convert from ellipsoidal to orthometric
            x, y, z = self._transformer_from_navd88.transform(coord.longitude_deg, coord.latitude_deg, coord.altitude_m)
            return Geographic(coord.latitude_deg, coord.longitude_deg, float(z))
        except Exception as e:
            self.logger.error(f"Error in ellipsoidal to orthometric conversion: {e}")
            raise


class Ellipsoidal_Datum(Base):
    """
    Ellipsoidal vertical datum (no geoid separation).

    This represents heights measured directly relative to the reference ellipsoid.
    Conversions between orthometric and ellipsoidal heights require an external
    geoid model (like EGM96).
    """

    def __init__(self, name: str = "Ellipsoidal", epsg_code: int | None = None):
        """Initialize ellipsoidal vertical datum."""
        super().__init__(name, epsg_code)

    def separation_meters(self, coord: Geographic) -> float:
        """Ellipsoidal datum has zero geoid separation."""
        return 0.0

    def to_ellipsoidal(self, coord: Geographic) -> Geographic:
        """
        Return the same coordinate (already in ellipsoidal height).

        Args:
            coord: Geographic coordinate with ellipsoidal height

        Returns:
            Same geographic coordinate
        """
        return coord

    def to_orthometric(self, coord: Geographic) -> Geographic:
        """
        Cannot convert from ellipsoidal to orthometric without geoid model.

        Args:
            coord: Geographic coordinate with ellipsoidal height

        Raises:
            NotImplementedError: Requires external geoid model
        """
        raise NotImplementedError("Cannot convert ellipsoidal to orthometric without geoid model")


# Common vertical datum instances
EGM96_DATUM = EGM96()
NAVD88_DATUM = NAVD88()
ELIPSOIDAL_DATUM = Ellipsoidal_Datum()


__all__ = [
    'Base',
    'EGM96',
    'NAVD88',
    'Ellipsoidal_Datum',
    'EGM96_DATUM',
    'NAVD88_DATUM',
    'ELIPSOIDAL_DATUM',
]
