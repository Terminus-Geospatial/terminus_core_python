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
#    File:    test_geographic.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for Geographic coordinate functionality.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import pytest

# Project Libraries
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.types import Type


# Fixtures for common objects
@pytest.fixture
def nyc_geographic():
    """New York City geographic coordinate."""
    return Geographic.create(40.7128, -74.0060, 10.5)

@pytest.fixture
def sydney_geographic():
    """Sydney geographic coordinate."""
    return Geographic.create(-33.8688, 151.2093, 58.0)

@pytest.fixture
def north_pole_geographic():
    """North pole geographic coordinate."""
    return Geographic.create(89.5, 0.0, 1000.0)

@pytest.fixture
def south_pole_geographic():
    """South pole geographic coordinate."""
    return Geographic.create(-89.5, 180.0, 500.0)


class Test_Geographic_Coordinate:
    """Test Geographic coordinate class."""

    @pytest.mark.parametrize("lat,lon,alt", [
        (40.7, -74.0, 10.5),
        (0.0, 0.0, None),
        (-33.9, 151.2, 100.0),
        (90.0, 0.0, 0.0),  # North pole
        (-90.0, 0.0, 0.0),  # South pole
    ])
    def test_geographic_creation(self, lat, lon, alt):
        """Test creating geographic coordinates."""
        geo = Geographic.create(lat, lon, alt)

        assert geo.latitude_deg == lat
        assert geo.longitude_deg == lon
        if alt is None:
            assert geo.altitude_m is None
        else:
            assert geo.altitude_m == alt

    def test_geographic_creation_with_altitude(self):
        """Test creating geographic coordinates with altitude."""
        geo = Geographic.create(40.7, -74.0, 10.5)
        assert geo.altitude_m == 10.5

    def test_geographic_creation_without_altitude(self):
        """Test creating geographic coordinates without altitude."""
        geo = Geographic.create(40.7, -74.0)
        assert geo.altitude_m is None

    def test_geographic_bounds_validation(self):
        """Test geographic coordinate bounds validation."""
        # Valid coordinates
        Geographic.create(0.0, 0.0)  # Equator, prime meridian
        Geographic.create(45.0, 90.0)  # Valid
        Geographic.create(-45.0, -180.0)  # Valid

        # Invalid latitude
        with pytest.raises(ValueError):
            Geographic.create(91.0, 0.0)  # Too far north

        with pytest.raises(ValueError):
            Geographic.create(-91.0, 0.0)  # Too far south

    def test_geographic_equality(self):
        """Test geographic coordinate equality."""
        geo1 = Geographic.create(40.7, -74.0, 10.5)
        geo2 = Geographic.create(40.7, -74.0, 10.5)
        geo3 = Geographic.create(40.7, -74.1, 10.5)  # Different longitude

        assert geo1 == geo2
        assert geo1 != geo3

    def test_geographic_hash(self):
        """Test geographic coordinate hashing."""
        geo1 = Geographic.create(40.7, -74.0, 10.5)
        geo2 = Geographic.create(40.7, -74.0, 10.5)

        assert hash(geo1) == hash(geo2)

    def test_geographic_string_representation(self):
        """Test geographic coordinate string representation."""
        geo = Geographic.create(40.7128, -74.0060, 10.5)
        str_repr = str(geo)

        assert "Geographic" in str_repr
        assert "40.7128" in str_repr
        assert "-74.0060" in str_repr
        assert "10.5" in str_repr

    def test_geographic_type(self):
        """Test geographic coordinate type."""
        geo = Geographic.create(40.7, -74.0, 10.5)
        assert geo.type() == Type.GEOGRAPHIC

    def test_geographic_copy(self):
        """Test geographic coordinate copying."""
        geo = Geographic.create(40.7, -74.0, 10.5)
        geo_copy = geo.copy()

        assert geo == geo_copy
        assert geo is not geo_copy

    def test_geographic_latitude_conversion(self):
        """Test latitude to radians conversion."""
        geo = Geographic.create(45.0, 0.0, 0.0)
        expected_rad = math.radians(45.0)
        assert abs(geo.lat_rad - expected_rad) < 1e-10

    def test_geographic_longitude_conversion(self):
        """Test longitude to radians conversion."""
        geo = Geographic.create(0.0, 90.0, 0.0)
        expected_rad = math.radians(90.0)
        assert abs(geo.lon_rad - expected_rad) < 1e-10

    def test_geographic_north_pole(self, north_pole_geographic):
        """Test north pole coordinate."""
        assert north_pole_geographic.latitude_deg == 89.5
        assert north_pole_geographic.longitude_deg == 0.0
        assert north_pole_geographic.altitude_m == 1000.0

    def test_geographic_south_pole(self, south_pole_geographic):
        """Test south pole coordinate."""
        assert south_pole_geographic.latitude_deg == -89.5
        assert south_pole_geographic.longitude_deg == 180.0
        assert south_pole_geographic.altitude_m == 500.0


    def test_geographic_distance_calculation(self, nyc_geographic, sydney_geographic):
        """Test distance calculation between geographic coordinates."""
        # Use static distance method
        distance = Geographic.distance(nyc_geographic, sydney_geographic)
        assert distance > 0  # Should be positive distance
        assert distance > 1000000  # Should be thousands of kilometers
