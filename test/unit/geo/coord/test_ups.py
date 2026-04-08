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
#    File:    test_ups.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for UPS coordinate functionality.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import numpy as np
import pytest

# Project Libraries
from tmns.geo.coord.crs import CRS
from tmns.geo.coord.types import Type
from tmns.geo.coord.ups import UPS


# Fixtures for common objects
@pytest.fixture
def ups_north_coordinate():
    """UPS North coordinate."""
    return UPS.create(2000000.0, 2000000.0, "N", 1000.0)

@pytest.fixture
def ups_south_coordinate():
    """UPS South coordinate."""
    return UPS.create(2500000.0, 1500000.0, "S", 500.0)


class Test_UPS_Coordinate:
    """Test UPS coordinate class."""

    @pytest.mark.parametrize("easting,northing,hemisphere,alt", [
        (2000000.0, 2000000.0, "N", 1000.0),
        (2500000.0, 1500000.0, "S", 500.0),
        (1000000.0, 1000000.0, "N", None),
        (3000000.0, 3000000.0, "S", 0.0),
    ])
    def test_ups_creation(self, easting, northing, hemisphere, alt):
        """Test creating UPS coordinates."""
        ups = UPS.create(easting, northing, hemisphere, alt)

        assert ups.easting_m == easting
        assert ups.northing_m == northing
        assert ups.hemisphere == hemisphere
        if alt is None:
            assert ups.altitude_m is None
        else:
            assert ups.altitude_m == alt

    def test_ups_creation_with_altitude(self):
        """Test creating UPS coordinates with altitude."""
        ups = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        assert ups.altitude_m == 1000.0

    def test_ups_creation_without_altitude(self):
        """Test creating UPS coordinates without altitude."""
        ups = UPS.create(2000000.0, 2000000.0, "N")
        assert ups.altitude_m is None

    def test_ups_hemisphere_validation(self):
        """Test UPS hemisphere validation."""
        # Valid hemispheres
        UPS.create(2000000.0, 2000000.0, "N")
        UPS.create(2000000.0, 2000000.0, "S")

        # Invalid hemispheres
        with pytest.raises(ValueError):
            UPS.create(2000000.0, 2000000.0, "E")

        with pytest.raises(ValueError):
            UPS.create(2000000.0, 2000000.0, "W")

    def test_ups_bounds_validation(self):
        """Test UPS coordinate bounds validation."""
        # Valid coordinates (within UPS bounds)
        UPS.create(0.0, 0.0, "N")  # Minimum
        UPS.create(4000000.0, 4000000.0, "N")  # Maximum

        # Invalid coordinates (outside UPS bounds)
        with pytest.raises(ValueError):
            UPS.create(-1000.0, 2000000.0, "N")  # Negative easting

        with pytest.raises(ValueError):
            UPS.create(2000000.0, -1000.0, "N")  # Negative northing

        with pytest.raises(ValueError):
            UPS.create(4000001.0, 2000000.0, "N")  # Too far east

    def test_ups_equality(self):
        """Test UPS coordinate equality."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        ups2 = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        ups3 = UPS.create(2000001.0, 2000000.0, "N", 1000.0)  # Different easting

        assert ups1 == ups2
        assert ups1 != ups3

    def test_ups_hash(self):
        """Test UPS coordinate hashing."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        ups2 = UPS.create(2000000.0, 2000000.0, "N", 1000.0)

        assert hash(ups1) == hash(ups2)

    def test_ups_string_representation(self):
        """Test UPS coordinate string representation."""
        ups = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        str_repr = str(ups)

        assert "2000000.0" in str_repr
        assert "N" in str_repr
        assert "1000.0" in str_repr

    def test_ups_type(self):
        """Test UPS coordinate type."""
        ups = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        assert ups.type() == Type.UPS

    def test_ups_copy(self):
        """Test UPS coordinate copying."""
        ups = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        ups_copy = ups.copy()

        assert ups == ups_copy
        assert ups is not ups_copy

    def test_ups_north_hemisphere(self, ups_north_coordinate):
        """Test north hemisphere UPS coordinate."""
        assert ups_north_coordinate.hemisphere == "N"
        assert ups_north_coordinate.easting_m == 2000000.0
        assert ups_north_coordinate.northing_m == 2000000.0
        assert ups_north_coordinate.altitude_m == 1000.0

    def test_ups_south_hemisphere(self, ups_south_coordinate):
        """Test south hemisphere UPS coordinate."""
        assert ups_south_coordinate.hemisphere == "S"
        assert ups_south_coordinate.easting_m == 2500000.0
        assert ups_south_coordinate.northing_m == 1500000.0
        assert ups_south_coordinate.altitude_m == 500.0


    def test_ups_distance_calculation(self, ups_north_coordinate):
        """Test distance calculation between UPS coordinates."""
        other = UPS.create(2100000.0, 2000000.0, "N", 1000.0)
        distance = UPS.distance(ups_north_coordinate, other)

        expected = 100000.0  # 100km difference in easting
        assert abs(distance - expected) < 1e-10

    def test_ups_bounds(self):
        """Test UPS coordinate bounds."""
        bounds = UPS.bounds()

        assert bounds.min_easting == 0.0
        assert bounds.max_easting == 4000000.0
        assert bounds.min_northing == 0.0
        assert bounds.max_northing == 4000000.0

    def test_ups_is_in_bounds(self, ups_north_coordinate):
        """Test UPS bounds checking."""
        assert ups_north_coordinate.is_in_bounds()

        # Test out of bounds by creating coordinate without validation
        out_of_bounds = UPS._create_without_validation(
            easting_m=4000001.0, northing_m=2000000.0,
            hemisphere="N", crs=CRS.from_epsg(32661)
        )
        assert not out_of_bounds.is_in_bounds()

    def test_ups_center_offset(self, ups_north_coordinate):
        """Test UPS center offset calculation."""
        center_offset = ups_north_coordinate.center_offset()
        assert center_offset.easting_m == 0.0  # 2000000.0 - 2000000.0
        assert center_offset.northing_m == 0.0  # 2000000.0 - 2000000.0

        # Test offset from center
        ups_offset = UPS.create(2100000.0, 1900000.0, "N")
        offset = ups_offset.center_offset()
        assert offset.easting_m == 100000.0  # 2100000.0 - 2000000.0
        assert offset.northing_m == -100000.0  # 1900000.0 - 2000000.0

    def test_ups_arithmetic_operations(self, ups_north_coordinate):
        """Test UPS coordinate arithmetic operations."""
        # Test addition (not typically meaningful for UPS, but should work)
        result = ups_north_coordinate + UPS.create(1000.0, 2000.0, "N")
        assert result.easting_m == 2001000.0
        assert result.northing_m == 2002000.0



class Test_UPS_Arithmetic:
    """Test UPS arithmetic operations."""

    def test_ups_addition_same_hemisphere(self):
        """Test UPS coordinate addition in same hemisphere."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        ups2 = UPS.create(1000.0, 2000.0, "N", 500.0)

        result = ups1 + ups2

        assert result.easting_m == 2001000.0
        assert result.northing_m == 2002000.0
        assert result.altitude_m == 1000.0  # First coordinate's altitude
        assert result.hemisphere == "N"

    def test_ups_subtraction_same_hemisphere(self):
        """Test UPS coordinate subtraction in same hemisphere."""
        ups1 = UPS.create(2001000.0, 2002000.0, "N", 1000.0)
        ups2 = UPS.create(1000.0, 2000.0, "N", 500.0)

        result = ups1 - ups2

        assert result.easting_m == 2000000.0
        assert result.northing_m == 2000000.0
        assert result.altitude_m == 1000.0  # First coordinate's altitude
        assert result.hemisphere == "N"

    def test_ups_addition_different_hemisphere_error(self):
        """Test UPS addition fails with different hemispheres."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2000000.0, 2000000.0, "S")

        with pytest.raises(ValueError, match="Cannot add UPS coordinates in different CRS"):
            ups1 + ups2

    def test_ups_subtraction_different_hemisphere_error(self):
        """Test UPS subtraction fails with different hemispheres."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2000000.0, 2000000.0, "S")

        with pytest.raises(ValueError, match="Cannot subtract UPS coordinates in different CRS"):
            ups1 - ups2

    def test_ups_addition_type_error(self):
        """Test UPS addition fails with non-UPS type."""
        ups = UPS.create(2000000.0, 2000000.0, "N")

        with pytest.raises(TypeError, match="Can only add UPS to UPS"):
            ups + "not_a_ups"

    def test_ups_subtraction_type_error(self):
        """Test UPS subtraction fails with non-UPS type."""
        ups = UPS.create(2000000.0, 2000000.0, "N")

        with pytest.raises(TypeError, match="Can only subtract UPS from UPS"):
            ups - "not_a_ups"


class Test_UPS_Calculations:
    """Test UPS bearing and distance calculations."""

    def test_ups_distance_same_hemisphere(self):
        """Test UPS distance calculation in same hemisphere."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N", 0.0)
        ups2 = UPS.create(2100000.0, 2100000.0, "N", 100.0)

        distance = UPS.distance(ups1, ups2)

        # Expected: sqrt(100000^2 + 100000^2 + 100^2) ≈ 141421.39159
        expected = math.sqrt(100000**2 + 100000**2 + 100**2)
        assert abs(distance - expected) < 1e-3  # More tolerant for floating point precision

    def test_ups_distance_with_altitude(self):
        """Test UPS distance calculation with altitude."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N", 0.0)
        ups2 = UPS.create(2100000.0, 2000000.0, "N", 100.0)

        distance = UPS.distance(ups1, ups2)

        # Should include altitude difference
        expected = math.sqrt(100000**2 + 100**2)
        assert abs(distance - expected) < 1e-3  # More tolerant for floating point precision

    def test_ups_distance_different_hemisphere_error(self):
        """Test UPS distance fails with different hemispheres."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2000000.0, 2000000.0, "S")

        with pytest.raises(ValueError, match="Cannot calculate distance between coordinates in different hemispheres"):
            UPS.distance(ups1, ups2)

    def test_ups_bearing_degrees(self):
        """Test UPS bearing calculation in degrees."""
        # North (same easting, higher northing)
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2000000.0, 2100000.0, "N")

        bearing = UPS.bearing(ups1, ups2, as_deg=True)
        assert abs(bearing - 0) < 1e-10  # North = 0°

        # East (higher easting, same northing)
        ups3 = UPS.create(2100000.0, 2000000.0, "N")
        bearing = UPS.bearing(ups1, ups3, as_deg=True)
        assert abs(bearing - 90) < 1e-10  # East = 90°

        # South (same easting, lower northing)
        bearing = UPS.bearing(ups2, ups1, as_deg=True)
        assert abs(bearing - 180) < 1e-10  # South = 180°

        # West (lower easting, same northing)
        bearing = UPS.bearing(ups3, ups1, as_deg=True)
        assert abs(bearing - 270) < 1e-10  # West = 270°

    def test_ups_bearing_radians(self):
        """Test UPS bearing calculation in radians."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2000000.0, 2100000.0, "N")

        bearing = UPS.bearing(ups1, ups2, as_deg=False)
        assert abs(bearing - 0) < 1e-10  # North = 0 radians

        # East
        ups3 = UPS.create(2100000.0, 2000000.0, "N")
        bearing = UPS.bearing(ups1, ups3, as_deg=False)
        assert abs(bearing - np.pi/2) < 1e-10  # East = Ï/2 radians

    def test_ups_bearing_different_hemisphere_error(self):
        """Test UPS bearing fails with different hemispheres."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2000000.0, 2000000.0, "S")

        with pytest.raises(ValueError, match="Cannot calculate bearing between coordinates in different hemispheres"):
            UPS.bearing(ups1, ups2)

    def test_ups_bearing_diagonal(self):
        """Test UPS bearing for diagonal movement."""
        ups1 = UPS.create(2000000.0, 2000000.0, "N")
        ups2 = UPS.create(2100000.0, 2100000.0, "N")  # Northeast

        bearing = UPS.bearing(ups1, ups2, as_deg=True)
        # Should be 45° (northeast)
        assert abs(bearing - 45) < 1e-10


class Test_UPS_Edge_Cases:
    """Test UPS edge cases and error conditions."""

    def test_ups_string_representation_with_altitude(self):
        """Test UPS string representation with altitude."""
        ups = UPS.create(2000000.0, 2000000.0, "N", 123.45)

        str_repr = str(ups)
        assert "2000000.00" in str_repr
        assert "N" in str_repr
        assert "123.45" in str_repr
        assert "altitude=" in str_repr

    def test_ups_string_representation_without_altitude(self):
        """Test UPS string representation without altitude."""
        ups = UPS.create(2000000.0, 2000000.0, "N")

        str_repr = str(ups)
        assert "2000000.00" in str_repr
        assert "N" in str_repr
        assert "altitude=None" in str_repr

    def test_ups_tuple_conversion(self):
        """Test UPS tuple conversion methods."""
        ups = UPS.create(2000000.0, 2000000.0, "N", 100.0)

        # Test 2D tuple
        tuple_2d = ups.to_tuple()
        assert tuple_2d == (2000000.0, 2000000.0)

        # Test 3D tuple
        tuple_3d = ups.to_3d_tuple()
        assert tuple_3d == (2000000.0, 2000000.0, 100.0)

        # Test 3D tuple with no altitude
        ups_no_alt = UPS.create(2000000.0, 2000000.0, "N")
        tuple_3d_no_alt = ups_no_alt.to_3d_tuple()
        assert tuple_3d_no_alt == (2000000.0, 2000000.0, 0.0)

    def test_ups_bounds_info(self):
        """Test UPS bounds information."""
        bounds = UPS.bounds()

        assert bounds.min_easting == 0.0
        assert bounds.max_easting == 4000000.0
        assert bounds.min_northing == 0.0
        assert bounds.max_northing == 4000000.0

    def test_ups_is_in_bounds(self):
        """Test UPS bounds checking."""
        # In bounds
        ups_in = UPS.create(2000000.0, 2000000.0, "N")
        assert ups_in.is_in_bounds()

        # Edge cases
        ups_edge_min = UPS.create(0.0, 0.0, "N")
        assert ups_edge_min.is_in_bounds()

        ups_edge_max = UPS.create(4000000.0, 4000000.0, "N")
        assert ups_edge_max.is_in_bounds()

        # Out of bounds - create without validation
        ups_out_easting = UPS._create_without_validation(
            easting_m=4000001.0, northing_m=2000000.0,
            hemisphere="N", crs=CRS.from_epsg(32661)
        )
        assert not ups_out_easting.is_in_bounds()

        ups_out_northing = UPS._create_without_validation(
            easting_m=2000000.0, northing_m=4000001.0,
            hemisphere="N", crs=CRS.from_epsg(32661)
        )
        assert not ups_out_northing.is_in_bounds()

    def test_ups_center_offset(self):
        """Test UPS center offset calculation."""
        # Center point
        ups_center = UPS.create(2000000.0, 2000000.0, "N")
        offset = ups_center.center_offset()
        assert offset.easting_m == 0.0  # 2000000.0 - 2000000.0
        assert offset.northing_m == 0.0  # 2000000.0 - 2000000.0

        # Offset from center
        ups_offset = UPS.create(2100000.0, 1900000.0, "N")
        offset = ups_offset.center_offset()
        assert offset.easting_m == 100000.0  # 2100000.0 - 2000000.0
        assert offset.northing_m == -100000.0  # 1900000.0 - 2000000.0
