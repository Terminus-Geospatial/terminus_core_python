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
#    File:    pixel.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Pixel coordinate implementation.
"""

# Python Standard Libraries
from dataclasses import dataclass
from typing import Union

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type


@dataclass
class Pixel:
    """Pixel/image coordinate."""
    x_px: float
    y_px: float

    @staticmethod
    def create(x_px: float, y_px: float) -> 'Pixel':
        """Create a pixel coordinate."""
        return Pixel(x_px=x_px, y_px=y_px)

    def type(self) -> Coordinate_Type:
        """Get the coordinate type."""
        return Coordinate_Type.PIXEL

    def to_tuple(self) -> tuple[float, float]:
        """Convert to (x, y) tuple."""
        return (self.x_px, self.y_px)

    def to_int_tuple(self) -> tuple[int, int]:
        """Convert to integer pixel coordinates."""
        return (int(self.x_px + 0.5), int(self.y_px + 0.5))

    def __str__(self) -> str:
        """String representation."""
        return f"({self.x_px:.1f}, {self.y_px:.1f})"

    def to_epsg(self) -> int:
        """Get EPSG code for this coordinate."""
        # Pixel coordinates don't have a standard EPSG code
        return -1

    @property
    def x(self) -> float:
        """Get x coordinate in pixels (backward compatibility)."""
        return self.x_px

    @property
    def y(self) -> float:
        """Get y coordinate in pixels (backward compatibility)."""
        return self.y_px


__all__ = [
    'Pixel',
]
