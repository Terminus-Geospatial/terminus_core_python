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
#    File:    test_utm.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for UTM coordinate functionality.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import numpy as np
import pytest

# Project Libraries
from tmns.geo.coord.utm import UTM
from tmns.geo.coord.crs import CRS
from tmns.geo.coord.types import Type


# Fixtures for common objects
@pytest.fixture
def utm_coordinate():
    """UTM coordinate."""
    return UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)

@pytest.fixture
def utm_southern_hemisphere():
    """UTM coordinate in southern hemisphere."""
    return UTM.create(500000, 4649776, CRS.utm_zone(33, 'S'), 100.0)


class Test_UTM_Coordinate:
    """Test UTM coordinate class."""

    @pytest.mark.parametrize("easting,northing,crs,alt", [
        (583000, 4507000, CRS.utm_zone(18, 'N'), 10.5),
        (500000, 4649776, CRS.utm_zone(33, 'S'), 100.0),
        (400000, 3700000, CRS.utm_zone(10, 'N'), None),
        (600000, 5400000, CRS.utm_zone(40, 'N'), 0.0),
    ])
    def test_utm_creation(self, easting, northing, crs, alt):
        """Test creating UTM coordinates."""
        utm = UTM.create(easting, northing, crs, alt)

        assert utm.easting_m == easting
        assert utm.northing_m == northing
        assert utm.crs == crs
        if alt is None:
            assert utm.altitude_m is None
        else:
            assert utm.altitude_m == alt

    def test_utm_creation_with_altitude(self):
        """Test creating UTM coordinates with altitude."""
        utm = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        assert utm.altitude_m == 10.5

    def test_utm_creation_without_altitude(self):
        """Test creating UTM coordinates without altitude."""
        utm = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'))
        assert utm.altitude_m is None

    def test_utm_zone_extraction(self):
        """Test UTM zone extraction from CRS code."""
        utm_north = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)  # Zone 18N
        utm_south = UTM.create(500000, 4649776, CRS.utm_zone(33, 'S'), 100.0)  # Zone 33S

        assert utm_north.zone_number == 18
        assert utm_north.hemisphere == "N"
        assert utm_south.zone_number == 33
        assert utm_south.hemisphere == "S"

    def test_utm_bounds_validation(self):
        """Test UTM coordinate bounds validation."""
        # Valid coordinates
        UTM.create(100000, 1000000, CRS.utm_zone(10, 'N'))  # Valid minimum
        UTM.create(900000, 9000000, CRS.utm_zone(10, 'N'))  # Valid maximum

        # Invalid easting (too small)
        with pytest.raises(ValueError, match="UTM easting.*is outside valid range"):
            UTM.create(49999, 4507000, CRS.utm_zone(18, 'N'))  # Below minimum

        # Invalid easting (too large)
        with pytest.raises(ValueError, match="UTM easting.*is outside valid range"):
            UTM.create(1000001, 4507000, CRS.utm_zone(18, 'N'))  # Above maximum

        # Invalid northing (negative)
        with pytest.raises(ValueError, match="UTM northing.*is outside valid range"):
            UTM.create(500000, -1, CRS.utm_zone(18, 'N'))  # Below minimum

        # Invalid northing (too large)
        with pytest.raises(ValueError, match="UTM northing.*is outside valid range"):
            UTM.create(500000, 10000001, CRS.utm_zone(18, 'N'))  # Above maximum

    def test_utm_equality(self):
        """Test UTM coordinate equality."""
        utm1 = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        utm2 = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        utm3 = UTM.create(583001, 4507000, CRS.utm_zone(18, 'N'), 10.5)  # Different easting

        assert utm1 == utm2
        assert utm1 != utm3

    def test_utm_hash(self):
        """Test UTM coordinate hashing."""
        utm1 = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        utm2 = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)

        assert hash(utm1) == hash(utm2)

    def test_utm_string_representation(self):
        """Test UTM coordinate string representation."""
        utm = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        str_repr = str(utm)

        assert "583000" in str_repr
        assert "4507000" in str_repr
        assert "EPSG:32618" in str_repr
        assert "10.5" in str_repr

    def test_utm_type(self):
        """Test UTM coordinate type."""
        utm = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        assert utm.type() == Type.UTM

    def test_utm_copy(self):
        """Test UTM coordinate copying."""
        utm = UTM.create(583000, 4507000, CRS.utm_zone(18, 'N'), 10.5)
        utm_copy = utm.copy()

        assert utm == utm_copy
        assert utm is not utm_copy

    def test_utm_northern_hemisphere(self, utm_coordinate):
        """Test northern hemisphere UTM coordinate."""
        assert utm_coordinate.hemisphere == "N"
        assert utm_coordinate.zone_number == 18
        assert utm_coordinate.crs.epsg_code == 32618

    def test_utm_southern_hemisphere(self, utm_southern_hemisphere):
        """Test southern hemisphere UTM coordinate."""
        assert utm_southern_hemisphere.hemisphere == "S"
        assert utm_southern_hemisphere.zone_number == 33
        assert utm_southern_hemisphere.crs.epsg_code == 32733

    def test_utm_central_meridian(self):
        """Test UTM central meridian calculation."""
        # Test various zones
        test_cases = [
            (1, 'N', -177),   # Zone 1: -177°
            (10, 'N', -123),  # Zone 10: -123°
            (18, 'N', -75),   # Zone 18: -75°
            (30, 'N', -3),    # Zone 30: -3°
            (60, 'N', 177),   # Zone 60: 177°
        ]

        for zone, hemisphere, expected in test_cases:
            utm = UTM.create(500000, 5000000, CRS.utm_zone(zone, hemisphere))
            assert abs(utm.central_meridian - expected) < 1e-10, f"Zone {zone} central meridian mismatch"


class Test_UTM_Arithmetic:
    """Test UTM arithmetic operations."""

    def test_utm_addition_same_zone(self):
        """Test UTM coordinate addition in same zone."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'), 100.0)
        utm2 = UTM.create(100000, 500000, CRS.utm_zone(10, 'N'), 50.0)

        result = utm1 + utm2

        assert result.easting_m == 600000
        assert result.northing_m == 4500000
        assert result.altitude_m == 100.0  # First coordinate's altitude
        assert result.crs == utm1.crs

    def test_utm_subtraction_same_zone(self):
        """Test UTM coordinate subtraction in same zone."""
        utm1 = UTM.create(600000, 4500000, CRS.utm_zone(10, 'N'), 100.0)
        utm2 = UTM.create(100000, 500000, CRS.utm_zone(10, 'N'), 50.0)

        result = utm1 - utm2

        assert result.easting_m == 500000
        assert result.northing_m == 4000000
        assert result.altitude_m == 100.0  # First coordinate's altitude
        assert result.crs == utm1.crs

    def test_utm_addition_different_zone_error(self):
        """Test UTM addition fails with different zones."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(500000, 4000000, CRS.utm_zone(11, 'N'))

        with pytest.raises(ValueError, match="Cannot add UTM coordinates in different CRS"):
            utm1 + utm2

    def test_utm_subtraction_different_zone_error(self):
        """Test UTM subtraction fails with different zones."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(500000, 4000000, CRS.utm_zone(11, 'N'))

        with pytest.raises(ValueError, match="Cannot subtract UTM coordinates in different CRS"):
            utm1 - utm2

    def test_utm_addition_type_error(self):
        """Test UTM addition fails with non-UTM type."""
        utm = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))

        with pytest.raises(TypeError, match="Can only add UTM to UTM"):
            utm + "not_a_utm"

    def test_utm_subtraction_type_error(self):
        """Test UTM subtraction fails with non-UTM type."""
        utm = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))

        with pytest.raises(TypeError, match="Can only subtract UTM from UTM"):
            utm - "not_a_utm"


class Test_UTM_Calculations:
    """Test UTM bearing and distance calculations."""

    def test_utm_distance_same_zone(self):
        """Test UTM distance calculation in same zone."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'), 0.0)
        utm2 = UTM.create(600000, 4100000, CRS.utm_zone(10, 'N'), 100.0)

        distance = UTM.distance(utm1, utm2)

        # Expected: sqrt(100000^2 + 100000^2 + 100^2) ÷ 141421.356
        expected = np.sqrt(100000**2 + 100000**2 + 100**2)
        assert abs(distance - expected) < 1e-6

    def test_utm_distance_no_altitude(self):
        """Test UTM distance calculation without altitude."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))  # No altitude
        utm2 = UTM.create(600000, 4100000, CRS.utm_zone(10, 'N'))  # No altitude

        distance = UTM.distance(utm1, utm2)

        # Expected: sqrt(100000^2 + 100000^2) ÷ 141421.356
        expected = np.sqrt(100000**2 + 100000**2)
        assert abs(distance - expected) < 1e-6

    def test_utm_distance_different_zone_error(self):
        """Test UTM distance fails with different zones."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(500000, 4000000, CRS.utm_zone(11, 'N'))

        with pytest.raises(ValueError, match="Cannot calculate distance between coordinates in different UTM zones"):
            UTM.distance(utm1, utm2)

    def test_utm_bearing_degrees(self):
        """Test UTM bearing calculation in degrees."""
        # North (same easting, higher northing)
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(500000, 4100000, CRS.utm_zone(10, 'N'))

        bearing = UTM.bearing(utm1, utm2, as_deg=True)
        assert abs(bearing - 0) < 1e-10  # North = 0°

        # East (higher easting, same northing)
        utm3 = UTM.create(510000, 4000000, CRS.utm_zone(10, 'N'))
        bearing = UTM.bearing(utm1, utm3, as_deg=True)
        assert abs(bearing - 90) < 1e-10  # East = 90°

        # South (same easting, lower northing)
        bearing = UTM.bearing(utm2, utm1, as_deg=True)
        assert abs(bearing - 180) < 1e-10  # South = 180°

        # West (lower easting, same northing)
        bearing = UTM.bearing(utm3, utm1, as_deg=True)
        assert abs(bearing - 270) < 1e-10  # West = 270°

    def test_utm_bearing_radians(self):
        """Test UTM bearing calculation in radians."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(500000, 4100000, CRS.utm_zone(10, 'N'))

        bearing = UTM.bearing(utm1, utm2, as_deg=False)
        assert abs(bearing - 0) < 1e-10  # North = 0 radians

        # East
        utm3 = UTM.create(510000, 4000000, CRS.utm_zone(10, 'N'))
        bearing = UTM.bearing(utm1, utm3, as_deg=False)
        assert abs(bearing - np.pi/2) < 1e-10  # East = Ï/2 radians

    def test_utm_bearing_different_zone_error(self):
        """Test UTM bearing fails with different zones."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(500000, 4000000, CRS.utm_zone(11, 'N'))

        with pytest.raises(ValueError, match="Cannot calculate bearing between coordinates in different UTM zones"):
            UTM.bearing(utm1, utm2)

    def test_utm_bearing_diagonal(self):
        """Test UTM bearing for diagonal movement."""
        utm1 = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        utm2 = UTM.create(600000, 4100000, CRS.utm_zone(10, 'N'))  # Northeast

        bearing = UTM.bearing(utm1, utm2, as_deg=True)
        # Should be 45° (northeast)
        assert abs(bearing - 45) < 1e-10


class Test_UTM_Edge_Cases:
    """Test UTM edge cases and error conditions."""

    def test_utm_default_crs(self):
        """Test UTM creation with default CRS."""
        utm = UTM.create(500000, 4000000)  # No CRS specified

        # Should default to zone 10N
        assert utm.crs.epsg_code == 32610
        assert utm.zone_number == 10
        assert utm.hemisphere == 'N'

    def test_utm_string_representation_with_altitude(self):
        """Test UTM string representation with altitude."""
        utm = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'), 123.45)

        str_repr = str(utm)
        assert "500000.00" in str_repr
        assert "4000000.00" in str_repr
        assert "123.45" in str_repr
        assert "altitude=" in str_repr

    def test_utm_string_representation_without_altitude(self):
        """Test UTM string representation without altitude."""
        utm = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))

        str_repr = str(utm)
        assert "500000.00" in str_repr
        assert "4000000.00" in str_repr
        assert "altitude=None" in str_repr

    def test_utm_tuple_conversion(self):
        """Test UTM tuple conversion methods."""
        utm = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'), 100.0)

        # Test 2D tuple
        tuple_2d = utm.to_tuple()
        assert tuple_2d == (500000, 4000000)

        # Test 3D tuple
        tuple_3d = utm.to_3d_tuple()
        assert tuple_3d == (500000, 4000000, 100.0)

        # Test 3D tuple with no altitude
        utm_no_alt = UTM.create(500000, 4000000, CRS.utm_zone(10, 'N'))
        tuple_3d_no_alt = utm_no_alt.to_3d_tuple()
        assert tuple_3d_no_alt == (500000, 4000000, 0.0)
