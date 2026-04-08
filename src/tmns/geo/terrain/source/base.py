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
#    File:    base.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Base elevation source class.

Provides the foundation for all elevation data sources with a consistent
interface and common functionality.
"""

# Python Standard Libraries
from abc import ABC, abstractmethod
from typing import Any

# Project Libraries
from tmns.geo.coord import Geographic
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.coord.vdatum import Base as VBase, ELIPSOIDAL_DATUM


class Base(ABC):
    """
    Abstract base class for elevation data sources.

    This class defines the interface that all elevation sources must implement.
    It provides common functionality for vertical datum handling.
    """

    def __init__(
        self,
        name: str,
        vertical_datum: VBase | None = None,
        interpolation: Interpolation_Method = Interpolation_Method.BILINEAR
    ):
        """
        Initialize elevation source.

        Args:
            name: Human-readable name of the elevation source
            vertical_datum: Vertical datum of the elevation data. Defaults to ellipsoidal.
            interpolation: Default interpolation method for elevation queries
        """
        self.name = name
        self.vertical_datum = vertical_datum or ELIPSOIDAL_DATUM
        self.interpolation = interpolation

    @abstractmethod
    def elevation_meters(self, coord: Geographic, target_datum: VBase | None = None) -> float | None:
        """
        Get elevation at the specified geographic coordinate.

        Args:
            coord: Geographic coordinate (latitude, longitude, altitude)
            target_datum: Target vertical datum for the elevation (optional)

        Returns:
            Elevation in meters in the target datum (or source datum if None),
            or None if no data available
        """
        pass

    @abstractmethod
    def contains(self, coord: Geographic) -> bool:
        """
        Check if this source contains elevation data for the specified coordinate.

        Args:
            coord: Geographic coordinate to check

        Returns:
            True if the source has data for this coordinate, False otherwise
        """
        pass


    def _convert_datum(self, elevation: float, target_datum: VBase, lat: float, lon: float) -> float:
        """
        Convert elevation from source datum to target datum.

        Args:
            elevation: Elevation value in source datum (meters)
            target_datum: Target vertical datum
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Elevation in target datum (meters)
        """
        # If source and target datums are the same, no conversion needed
        if self.vertical_datum == target_datum:
            return elevation

        # Convert from source datum to ellipsoidal, then to target datum
        if self.vertical_datum != ELIPSOIDAL_DATUM:
            h_ellip = self.vertical_datum.orthometric_to_ellipsoidal(lat, lon, elevation)
        else:
            h_ellip = elevation

        if target_datum != ELIPSOIDAL_DATUM:
            h_target = target_datum.ellipsoidal_to_orthometric(lat, lon, h_ellip)
        else:
            h_target = h_ellip

        return h_target

    def info(self) -> dict[str, Any]:
        """
        Get information about this elevation source.

        Returns:
            Dictionary containing source information
        """
        return {
            'name': self.name,
            'vertical_datum': self.vertical_datum.name,
            'interpolation': self.interpolation.name,
            'type': self.__class__.__name__,
        }

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.name})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"{self.__class__.__name__}(name='{self.name}', datum='{self.vertical_datum.name}')"


