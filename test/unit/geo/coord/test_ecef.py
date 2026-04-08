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
#    File:    test_ecef.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for ECEF coordinate functionality.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import pytest

# Project Libraries
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.types import Type


# Fixtures for common objects
@pytest.fixture
def ecef_coordinate():
    """ECEF coordinate."""
    return ECEF.create(-2700000, -4300000, 3850000)


class Test_ECEF_Coordinate:
    """Test ECEF coordinate functionality."""

    @pytest.mark.parametrize("x,y,z", [
        (-2700000, -4300000, 3850000),
        (0.0, 0.0, 6378137.0),  # On Earth surface at equator, prime meridian
        (6378137.0, 0.0, 0.0),  # On Earth surface at equator, 90°E
        (0.0, 6378137.0, 0.0),  # On Earth surface at equator, 90°N
        (0.0, 0.0, -6378137.0),  # On Earth surface at equator, 90°S
    ])
    def test_ecef_creation(self, x, y, z):
        """Test creating ECEF coordinates."""
        ecef = ECEF.create(x, y, z)

        assert ecef.x_m == x
        assert ecef.y_m == y
        assert ecef.z_m == z

    def test_ecef_creation_with_altitude(self):
        """Test creating ECEF coordinates with altitude."""
        ecef = ECEF.create(-2700000, -4300000, 3850000)
        assert ecef.z_m == 3850000

    def test_ecef_equality(self):
        """Test ECEF coordinate equality."""
        ecef1 = ECEF.create(-2700000, -4300000, 3850000)
        ecef2 = ECEF.create(-2700000, -4300000, 3850000)
        ecef3 = ECEF.create(-2700001, -4300000, 3850000)  # Different x

        assert ecef1 == ecef2
        assert ecef1 != ecef3

    def test_ecef_hash(self):
        """Test ECEF coordinate hashing."""
        ecef1 = ECEF.create(-2700000, -4300000, 3850000)
        ecef2 = ECEF.create(-2700000, -4300000, 3850000)

        assert hash(ecef1) == hash(ecef2)

    def test_ecef_string_representation(self):
        """Test ECEF coordinate string representation."""
        ecef = ECEF.create(-2700000, -4300000, 3850000)
        str_repr = str(ecef)

        assert "ECEF" in str_repr
        assert "-2700000" in str_repr
        assert "-4300000" in str_repr
        assert "3850000" in str_repr

    def test_ecef_type(self):
        """Test ECEF coordinate type."""
        ecef = ECEF.create(-2700000, -4300000, 3850000)
        assert ecef.type() == Type.ECEF

    def test_ecef_copy(self):
        """Test ECEF coordinate copying."""
        ecef = ECEF.create(-2700000, -4300000, 3850000)
        ecef_copy = ecef.copy()

        assert ecef == ecef_copy
        assert ecef is not ecef_copy

    def test_ecef_magnitude(self, ecef_coordinate):
        """Test ECEF coordinate magnitude calculation."""
        magnitude = ecef_coordinate.magnitude
        expected = math.sqrt((-2700000)**2 + (-4300000)**2 + 3850000**2)
        assert abs(magnitude - expected) < 1e-10


    def test_ecef_distance_calculation(self, ecef_coordinate):
        """Test distance calculation between ECEF coordinates."""
        other = ECEF.create(-2700001, -4300001, 3850001)
        distance = ECEF.distance(ecef_coordinate, other)

        expected = math.sqrt(1**2 + 1**2 + 1**2)
        assert abs(distance - expected) < 1e-10


    def test_ecef_arithmetic_operations(self, ecef_coordinate):
        """Test ECEF coordinate arithmetic operations."""
        # Test addition
        result = ecef_coordinate + ECEF.create(1000.0, 2000.0, 3000.0)
        assert result.x_m == -2699000.0
        assert result.y_m == -4298000.0
        assert result.z_m == 3853000.0

        # Test subtraction
        result = ecef_coordinate - ECEF.create(1000.0, 2000.0, 3000.0)
        assert result.x_m == -2701000.0
        assert result.y_m == -4302000.0
        assert result.z_m == 3847000.0
