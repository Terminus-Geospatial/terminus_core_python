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

Pixel coordinates represent discrete positions within an image or display system.
Unlike geographic or projected coordinate systems, pixel coordinates are
relative to a specific image or raster grid and have no absolute geographic
reference. They are commonly used in computer vision, image processing,
and GUI applications.

Pixel coordinates typically have their origin (0,0) at the top-left corner
of an image, with x increasing to the right and y increasing downward.
"""

# Python Standard Libraries
from dataclasses import dataclass
from typing import Union

# Project Libraries
from tmns.geo.coord.types import Type


@dataclass
class Pixel:
    """
    Pixel/image coordinate representing discrete grid positions.

    Represents a coordinate in pixel space, typically used for image processing,
    computer vision, and GUI applications. Pixel coordinates are relative to
    a specific image or display system and have no absolute geographic reference.

    Attributes:
        x_px: X coordinate in pixels (horizontal position, typically from left)
        y_px: Y coordinate in pixels (vertical position, typically from top)
    """
    x_px: float
    y_px: float

    @staticmethod
    def create(x_px: float, y_px: float) -> Pixel:
        """
        Create a pixel coordinate.

        Args:
            x_px: X coordinate in pixels
            y_px: Y coordinate in pixels

        Returns:
            Pixel coordinate instance
        """
        return Pixel(x_px=x_px, y_px=y_px)

    def type(self) -> Type:
        """
        Get the coordinate type.

        Returns:
            Type.PIXEL enum value
        """
        return Type.PIXEL

    def to_tuple(self) -> tuple[float, float]:
        """
        Convert to (x, y) tuple.

        Returns:
            Tuple containing (x_px, y_px)
        """
        return (self.x_px, self.y_px)

    def to_int_tuple(self) -> tuple[int, int]:
        """
        Convert to integer pixel coordinates.

        Rounds pixel coordinates to the nearest integer using standard
        rounding (0.5 rounds up). This is useful when converting to
        discrete pixel indices for image array access.

        Returns:
            Tuple of integer pixel coordinates
        """
        return (int(self.x_px + 0.5), int(self.y_px + 0.5))

    def __hash__(self) -> int:
        """
        Make Pixel hashable for use in sets and as dictionary keys.

        Returns:
            Hash value based on pixel coordinates
        """
        return hash((self.x_px, self.y_px))

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Pixel coordinate.

        Args:
            other: Object to compare against

        Returns:
            True if coordinates are identical, False otherwise
        """
        if not isinstance(other, Pixel):
            return False
        return (self.x_px == other.x_px and self.y_px == other.y_px)

    def __str__(self) -> str:
        """
        String representation of the coordinate.

        Returns:
            Human-readable string representation with one decimal place
        """
        return f"Pixel(x={self.x_px:.1f}, y={self.y_px:.1f})"

    @property
    def x(self) -> float:
        """
        Get x coordinate in pixels (backward compatibility).

        Returns:
            X pixel coordinate
        """
        return self.x_px

    @property
    def y(self) -> float:
        """
        Get y coordinate in pixels (backward compatibility).

        Returns:
            Y pixel coordinate
        """
        return self.y_px

    def copy(self) -> Pixel:
        """
        Create a copy of this pixel coordinate.

        Returns:
            New Pixel instance with same coordinates
        """
        return Pixel.create(self.x_px, self.y_px)

    def __add__(self, other: Pixel) -> Pixel:
        """
        Add two pixel coordinates.

        Args:
            other: Another Pixel coordinate

        Returns:
            New Pixel with summed coordinates
        """
        if not isinstance(other, Pixel):
            return NotImplemented
        return Pixel.create(self.x_px + other.x_px, self.y_px + other.y_px)

    def __sub__(self, other: Pixel) -> Pixel:
        """
        Subtract two pixel coordinates.

        Args:
            other: Another Pixel coordinate

        Returns:
            New Pixel with difference coordinates
        """
        if not isinstance(other, Pixel):
            return NotImplemented
        return Pixel.create(self.x_px - other.x_px, self.y_px - other.y_px)

    @staticmethod
    def distance(pixel1: Pixel, pixel2: Pixel) -> float:
        """
        Calculate Euclidean distance between two pixel coordinates.

        Args:
            pixel1: First pixel coordinate
            pixel2: Second pixel coordinate

        Returns:
            Euclidean distance in pixels
        """
        if not isinstance(pixel1, Pixel) or not isinstance(pixel2, Pixel):
            raise TypeError("Both arguments must be Pixel coordinates")

        dx = pixel1.x_px - pixel2.x_px
        dy = pixel1.y_px - pixel2.y_px
        return (dx * dx + dy * dy) ** 0.5


    def round(self) -> Pixel:
        """
        Round pixel coordinates to nearest integer.

        Returns:
            New Pixel with rounded coordinates
        """
        return Pixel.create(round(self.x_px), round(self.y_px))

    def floor(self) -> Pixel:
        """
        Floor pixel coordinates to integer.

        Returns:
            New Pixel with floored coordinates
        """
        return Pixel.create(int(self.x_px), int(self.y_px))

    def ceil(self) -> Pixel:
        """
        Ceil pixel coordinates to integer.

        Returns:
            New Pixel with ceiled coordinates
        """
        from math import ceil
        return Pixel.create(ceil(self.x_px), ceil(self.y_px))

