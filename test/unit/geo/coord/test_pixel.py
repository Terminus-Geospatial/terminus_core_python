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
#    File:    test_pixel.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for Pixel coordinate functionality.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import numpy as np
import pytest

# Project Libraries
from tmns.geo.coord.pixel import Pixel
from tmns.geo.coord.types import Type


# Fixtures for common objects
@pytest.fixture
def pixel_coordinate():
    """Pixel coordinate."""
    return Pixel.create(256.5, 128.3)


class Test_Pixel_Coordinate:
    """Test Pixel coordinate class."""

    @pytest.mark.parametrize("x,y", [
        (256.5, 128.3),
        (0.0, 0.0),
        (1024.0, 768.0),
        (100.5, 200.75),
        (-50.0, -100.0),
    ])
    def test_pixel_creation(self, x, y):
        """Test creating pixel coordinates."""
        pixel = Pixel.create(x, y)

        assert pixel.x == x
        assert pixel.y == y

    def test_pixel_equality(self):
        """Test pixel coordinate equality."""
        pixel1 = Pixel.create(256.5, 128.3)
        pixel2 = Pixel.create(256.5, 128.3)
        pixel3 = Pixel.create(256.6, 128.3)  # Different x

        assert pixel1 == pixel2
        assert pixel1 != pixel3

    def test_pixel_hash(self):
        """Test pixel coordinate hashing."""
        pixel1 = Pixel.create(256.5, 128.3)
        pixel2 = Pixel.create(256.5, 128.3)

        assert hash(pixel1) == hash(pixel2)

    def test_pixel_string_representation(self):
        """Test pixel coordinate string representation."""
        pixel = Pixel.create(256.5, 128.3)
        str_repr = str(pixel)

        assert "256.5" in str_repr
        assert "128.3" in str_repr

    def test_pixel_type(self):
        """Test pixel coordinate type."""
        pixel = Pixel.create(256.5, 128.3)
        assert pixel.type() == Type.PIXEL

    def test_pixel_copy(self):
        """Test pixel coordinate copying."""
        pixel = Pixel.create(256.5, 128.3)
        pixel_copy = pixel.copy()

        assert pixel == pixel_copy
        assert pixel is not pixel_copy

    def test_pixel_arithmetic_operations(self, pixel_coordinate):
        """Test pixel coordinate arithmetic operations."""
        # Test addition
        result = pixel_coordinate + Pixel.create(10.0, 20.0)
        assert result.x == 266.5
        assert result.y == 148.3

        # Test subtraction
        result = pixel_coordinate - Pixel.create(10.0, 20.0)
        assert result.x == 246.5
        assert abs(result.y - 108.3) < 1e-10  # Account for floating point precision

    def test_pixel_distance_calculation(self, pixel_coordinate):
        """Test distance calculation between pixel coordinates."""
        other = Pixel.create(356.5, 228.3)
        distance = Pixel.distance(pixel_coordinate, other)

        expected = math.sqrt((100.0)**2 + (100.0)**2)
        assert abs(distance - expected) < 1e-10

    def test_pixel_rounding(self):
        """Test pixel coordinate rounding."""
        pixel = Pixel.create(256.7, 128.3)
        rounded = pixel.round()

        assert rounded.x == 257
        assert rounded.y == 128

    def test_pixel_floor(self):
        """Test pixel coordinate floor."""
        pixel = Pixel.create(256.7, 128.3)
        floored = pixel.floor()

        assert floored.x == 256
        assert floored.y == 128

    def test_pixel_ceil(self):
        """Test pixel coordinate ceil."""
        pixel = Pixel.create(256.7, 128.3)
        ceiled = pixel.ceil()

        assert ceiled.x == 257
        assert ceiled.y == 129
