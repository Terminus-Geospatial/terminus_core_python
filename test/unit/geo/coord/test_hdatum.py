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
#    File:    test_datum.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Unit tests for datum definitions.
"""

import math
import numpy as np
import pytest

# Project Libraries
from tmns.geo.hdatum import Base as HBase, WGS84
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.ecef import ECEF


class Test_HBase:
    """Test HBase base class."""

    def test_semi_minor_axis_calculation(self):
        """Test semi-minor axis calculation."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)
        expected_b = 6378137.0 * (1 - 1.0 / 298.257223563)
        assert abs(datum.semi_minor_axis - expected_b) < 1e-6

    def test_ray_ellipsoid_intersection_simple(self):
        """Test simple ray-ellipsoid intersection."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        # Ray from above north pole pointing straight down
        origin = ECEF.create(0, 0, 7000000)  # 7000 km above pole
        direction = np.array([0, 0, -1])     # Pointing down

        intersection = datum.ray_ellipsoid_intersection(origin, direction)

        # Should intersect near the north pole
        assert abs(intersection.latitude_deg - 90.0) < 0.1
        assert abs(intersection.longitude_deg) < 0.1

    def test_ray_ellipsoid_intersection_misses(self):
        """Test ray that misses the ellipsoid."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        # Ray pointing away from ellipsoid
        origin = ECEF.create(0, 0, 7000000)
        direction = np.array([0, 0, 1])  # Pointing up

        with pytest.raises(ValueError, match="Ray does not intersect ellipsoid in forward direction."):
            datum.ray_ellipsoid_intersection(origin, direction)

    def test_check_ray_ellipsoid_intersection(self):
        """Test ray intersection check method."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        # Ray that should intersect
        origin = ECEF.create(0, 0, 7000000)
        direction = np.array([0, 0, -1])
        assert datum.check_ray_ellipsoid_intersection(origin, direction) is True

        # Ray that should not intersect
        direction = np.array([0, 0, 1])
        assert datum.check_ray_ellipsoid_intersection(origin, direction) is False

    def test_ray_ellipsoid_intersection_with_geographic_origin(self):
        """Test ray intersection with geographic origin."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        # Use geographic coordinate as origin
        origin_geo = Geographic.create(45.0, 0.0, 10000)  # 45°N, 0°E, 10km altitude
        direction = np.array([0, -1, -1])  # Pointing down and south

        intersection = datum.ray_ellipsoid_intersection(origin_geo, direction)

        # Should be on the surface (altitude close to 0)
        assert abs(intersection.altitude_m) < 100  # Within 100m of surface


class Test_WGS84:
    """Test WGS84 specific implementation."""

    def test_wgs84_parameters(self):
        """Test WGS84 standard parameters."""
        wgs84 = WGS84()

        # Standard WGS84 parameters
        assert abs(wgs84.semi_major_axis - 6378137.0) < 1e-6
        assert abs(wgs84.flattening - (1.0 / 298.257223563)) < 1e-12

        # Semi-minor axis should be approximately 6356752.314m
        expected_b = 6378137.0 * (1 - 1.0 / 298.257223563)
        assert abs(wgs84.semi_minor_axis - expected_b) < 1e-3

    def test_wgs84_ray_intersection_equator(self):
        """Test ray intersection at equator."""
        wgs84 = WGS84()

        # Ray from above equator pointing down
        origin = ECEF.create(6378137.0, 0, 15000)  # 15km above equator at prime meridian
        direction = np.array([0, 0, -1])

        # This should intersect at equator, prime meridian
        intersection = wgs84.ray_ellipsoid_intersection(origin, direction)

        # Should intersect at equator, prime meridian
        assert abs(intersection.latitude_deg) < 0.01
        assert abs(intersection.longitude_deg) < 0.01
        assert abs(intersection.altitude_m) < 1.0


class Test_HBase_Error_Cases:
    """Test error cases and edge conditions."""

    def test_invalid_direction_vector(self):
        """Test invalid direction vector (zero magnitude)."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        origin = ECEF.create(0, 0, 7000000)
        direction = np.array([0, 0, 0])  # Zero vector

        with pytest.raises(ValueError, match="Invalid direction vector"):
            datum.ray_ellipsoid_intersection(origin, direction)

    def test_very_small_direction_vector(self):
        """Test very small direction vector."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        origin = ECEF.create(0, 0, 7000000)
        direction = np.array([1e-15, 0, -1])  # Very small x component

        # Should still work
        intersection = datum.ray_ellipsoid_intersection(origin, direction)
        assert intersection is not None

    def test_ray_origin_inside_ellipsoid(self):
        """Test ray originating inside ellipsoid."""
        datum = HBase(semi_major_axis=6378137.0, flattening=1.0 / 298.257223563)

        # Origin at center of Earth
        origin = ECEF.create(0, 0, 0)
        direction = np.array([1, 0, 0])  # Pointing east

        # Should still find intersection
        intersection = datum.ray_ellipsoid_intersection(origin, direction)
        assert intersection is not None
        assert abs(intersection.altitude_m) < 1.0  # On surface
