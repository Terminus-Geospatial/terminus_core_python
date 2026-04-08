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
#    File:    flat.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Flat elevation source implementation.

Provides a constant elevation value for all coordinates. Useful for testing,
simulation, or areas with uniform elevation.
"""

# Python Standard Libraries
from typing import Any

# Project Libraries
from tmns.geo.coord import Geographic
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.source.base import Base
from tmns.geo.coord.vdatum import Base as VBase, ELIPSOIDAL_DATUM


class Flat(Base):
    """Flat elevation source with constant elevation value."""

    def __init__(
        self,
        elevation: float,
        name: str = "Flat Surface",
        vertical_datum: VBase | None = None,
        interpolation: Interpolation_Method = Interpolation_Method.NEAREST
    ):
        """
        Initialize flat elevation source.

        Args:
            elevation: Constant elevation value in meters
            name: Human-readable name for this source
            vertical_datum: Vertical datum of the elevation data. Defaults to ellipsoidal.
            interpolation: Interpolation method (not used for flat source but kept for interface consistency)
        """
        super().__init__(name, vertical_datum, interpolation)
        self.elevation = elevation

    def contains(self, coord: Geographic) -> bool:
        """
        Check if this source contains data for the specified coordinate.

        Args:
            coord: Geographic coordinate to check

        Returns:
            Always True for flat source (covers entire globe)
        """
        return True

    def elevation_meters(self, coord: Geographic, target_datum: VBase | None = None) -> float | None:
        """
        Get elevation at the specified geographic coordinate.

        Args:
            coord: Geographic coordinate (latitude, longitude, altitude)
            target_datum: Target vertical datum for the elevation (optional)

        Returns:
            Elevation in meters in the target datum (or source datum if None)
        """
        if target_datum is None or target_datum == self.vertical_datum:
            return self.elevation

        # Use the parent class method to handle datum conversion
        return self._convert_datum(self.elevation, target_datum, coord.latitude_deg, coord.longitude_deg)

    def info(self) -> dict[str, Any]:
        """Get detailed information about this flat elevation source."""
        info = super().info()
        info.update({
            'elevation': self.elevation,
            'coverage': 'global',
            'description': f'Constant elevation surface at {self.elevation}m',
        })
        return info

    def set_elevation(self, elevation: float) -> None:
        """
        Update the constant elevation value.

        Args:
            elevation: New elevation value in meters
        """
        self.elevation = elevation
