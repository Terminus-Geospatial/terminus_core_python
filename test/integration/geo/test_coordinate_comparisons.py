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
#    File:    test_coordinate_comparisons.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Integration tests comparing bearing and distance calculations across coordinate types.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import pytest

# Project Libraries
from tmns.geo.coord import (
    Geographic,
    Transformer,
)


class Test_Type_Comparisons:
    """Integration tests comparing bearing and distance across coordinate types."""

    @pytest.fixture
    def boston_geographic(self):
        """Boston geographic coordinate."""
        return Geographic.create(42.3601, -71.0589, 10.0)  # Boston, MA

    @pytest.fixture
    def nyc_geographic(self):
        """NYC geographic coordinate."""
        return Geographic.create(40.7128, -74.0060, 10.0)  # NYC, NY

    @pytest.fixture
    def transformer(self):
        """Coordinate transformer instance."""
        return Transformer()

    def test_geographic_to_utm_consistency(self, transformer, boston_geographic, nyc_geographic):
        """Test consistency between geographic and UTM coordinates."""
        # Convert both coordinates to UTM
        boston_utm = transformer.geo_to_utm(boston_geographic)
        nyc_utm = transformer.geo_to_utm(nyc_geographic)

        # Convert back to geographic
        boston_geo_back = transformer.utm_to_geo(boston_utm)
        nyc_geo_back = transformer.utm_to_geo(nyc_utm)

        # Should be very close to original (allowing for floating point error)
        assert abs(boston_geo_back.latitude_deg - boston_geographic.latitude_deg) < 1e-6
        assert abs(boston_geo_back.longitude_deg - boston_geographic.longitude_deg) < 1e-6
        assert abs(boston_geo_back.altitude_m - boston_geographic.altitude_m) < 1e-3

        assert abs(nyc_geo_back.latitude_deg - nyc_geographic.latitude_deg) < 1e-6
        assert abs(nyc_geo_back.longitude_deg - nyc_geographic.longitude_deg) < 1e-6
        assert abs(nyc_geo_back.altitude_m - nyc_geographic.altitude_m) < 1e-3

    def test_geographic_to_web_mercator_consistency(self, transformer, boston_geographic):
        """Test consistency between geographic and Web Mercator coordinates."""
        # Convert to Web Mercator
        boston_wm = transformer.geo_to_web_mercator(boston_geographic)

        # Convert back to geographic
        boston_geo_back = transformer.web_mercator_to_geo(boston_wm)

        # Should be very close to original
        assert abs(boston_geo_back.latitude_deg - boston_geographic.latitude_deg) < 1e-6
        assert abs(boston_geo_back.longitude_deg - boston_geographic.longitude_deg) < 1e-6
        assert abs(boston_geo_back.altitude_m - boston_geographic.altitude_m) < 1e-3

    def test_geographic_to_ecef_consistency(self, transformer, boston_geographic):
        """Test consistency between geographic and ECEF coordinates."""
        # Convert to ECEF
        boston_ecef = transformer.geo_to_ecef(boston_geographic)

        # Convert back to geographic
        boston_geo_back = transformer.ecef_to_geo(boston_ecef)

        # Should be very close to original
        assert abs(boston_geo_back.latitude_deg - boston_geographic.latitude_deg) < 1e-6
        assert abs(boston_geo_back.longitude_deg - boston_geographic.longitude_deg) < 1e-6
        assert abs(boston_geo_back.altitude_m - boston_geographic.altitude_m) < 1e-3

    def test_utm_to_web_mercator_via_geographic(self, transformer, boston_geographic):
        """Test UTM to Web Mercator conversion via geographic."""
        # Geographic -> UTM -> Geographic -> Web Mercator
        boston_utm = transformer.geo_to_utm(boston_geographic)
        boston_geo_via_utm = transformer.utm_to_geo(boston_utm)
        boston_wm_via_utm = transformer.geo_to_web_mercator(boston_geo_via_utm)

        # Direct Geographic -> Web Mercator
        boston_wm_direct = transformer.geo_to_web_mercator(boston_geographic)

        # Should be very close
        assert abs(boston_wm_via_utm.easting_m - boston_wm_direct.easting_m) < 1e-3
        assert abs(boston_wm_via_utm.northing_m - boston_wm_direct.northing_m) < 1e-3
        assert abs(boston_wm_via_utm.altitude_m - boston_wm_direct.altitude_m) < 1e-3

    def test_distance_calculations_consistency(self, transformer, boston_geographic, nyc_geographic):
        """Test that distance calculations are consistent across coordinate types."""
        # Calculate distance in geographic coordinates (haversine)
        geo_distance = self._haversine_distance(boston_geographic, nyc_geographic)

        # Convert to UTM and calculate Euclidean distance
        boston_utm = transformer.geo_to_utm(boston_geographic)
        nyc_utm = transformer.geo_to_utm(nyc_geographic)
        utm_distance = math.sqrt(
            (nyc_utm.easting_m - boston_utm.easting_m)**2 +
            (nyc_utm.northing_m - boston_utm.northing_m)**2
        )

        # Convert to Web Mercator and calculate Euclidean distance
        boston_wm = transformer.geo_to_web_mercator(boston_geographic)
        nyc_wm = transformer.geo_to_web_mercator(nyc_geographic)
        wm_distance = math.sqrt(
            (nyc_wm.easting_m - boston_wm.easting_m)**2 +
            (nyc_wm.northing_m - boston_wm.northing_m)**2
        )

        # Distances should be reasonably close (within a few percent)
        # UTM should be closest to true geographic distance
        assert abs(utm_distance - geo_distance) / geo_distance < 0.03  # Within 3% (more realistic for long distances)
        assert abs(wm_distance - geo_distance) / geo_distance < 0.40  # Within 40% (Web Mercator has significant distortion)

    def test_polar_regions(self, transformer):
        """Test coordinate transformations in polar regions."""
        # North pole
        north_pole_geo = Geographic.create(89.9, 0.0, 1000.0)
        north_pole_ups = transformer.geo_to_ups(north_pole_geo)
        north_pole_geo_back = transformer.ups_to_geo(north_pole_ups)

        assert abs(north_pole_geo_back.latitude_deg - north_pole_geo.latitude_deg) < 1e-6
        assert abs(north_pole_geo_back.longitude_deg - north_pole_geo.longitude_deg) < 1e-6
        assert abs(north_pole_geo_back.altitude_m - north_pole_geo.altitude_m) < 1e-3

        # South pole
        south_pole_geo = Geographic.create(-89.9, 180.0, 500.0)
        south_pole_ups = transformer.geo_to_ups(south_pole_geo)
        south_pole_geo_back = transformer.ups_to_geo(south_pole_ups)

        assert abs(south_pole_geo_back.latitude_deg - south_pole_geo.latitude_deg) < 1e-6
        assert abs(south_pole_geo_back.longitude_deg - south_pole_geo.longitude_deg) < 1e-6
        assert abs(south_pole_geo_back.altitude_m - south_pole_geo.altitude_m) < 1e-3

    def test_dateline_crossing(self, transformer):
        """Test coordinate transformations crossing the international dateline."""
        # Coordinates on either side of dateline
        west_of_dateline = Geographic.create(35.0, 179.0, 100.0)
        east_of_dateline = Geographic.create(35.0, -179.0, 100.0)

        # Convert to UTM
        west_utm = transformer.geo_to_utm(west_of_dateline)
        east_utm = transformer.geo_to_utm(east_of_dateline)

        # Convert back
        west_geo_back = transformer.utm_to_geo(west_utm)
        east_geo_back = transformer.utm_to_geo(east_utm)

        # Should maintain positions relative to dateline
        assert abs(west_geo_back.latitude_deg - west_of_dateline.latitude_deg) < 1e-6
        assert abs(east_geo_back.latitude_deg - east_of_dateline.latitude_deg) < 1e-6

        # Longitude should be close (may wrap around)
        assert abs(abs(west_geo_back.longitude_deg) - 179.0) < 1e-6
        assert abs(abs(east_geo_back.longitude_deg) - 179.0) < 1e-6

    def test_ecef_precision(self, transformer):
        """Test ECEF coordinate precision and stability."""
        # Test with high-precision coordinates
        precise_geo = Geographic.create(40.712812345678, -74.006012345678, 10.123456789)

        # Multiple roundtrips through ECEF
        current_geo = precise_geo
        for _ in range(10):
            ecef = transformer.geo_to_ecef(current_geo)
            current_geo = transformer.ecef_to_geo(ecef)

        # Should maintain precision
        assert abs(current_geo.latitude_deg - precise_geo.latitude_deg) < 1e-8
        assert abs(current_geo.longitude_deg - precise_geo.longitude_deg) < 1e-8
        assert abs(current_geo.altitude_m - precise_geo.altitude_m) < 1e-4

    def test_coordinate_type_chains(self, transformer, boston_geographic):
        """Test chains of coordinate type conversions."""
        # Test various conversion chains
        chains = [
            # Geographic -> UTM -> Web Mercator -> Geographic
            ['geo_to_utm', 'utm_to_geo', 'geo_to_web_mercator', 'web_mercator_to_geo'],

            # Geographic -> ECEF -> UTM -> Geographic
            ['geo_to_ecef', 'ecef_to_geo', 'geo_to_utm', 'utm_to_geo'],

            # Geographic -> Web Mercator -> UTM -> ECEF -> Geographic
            ['geo_to_web_mercator', 'web_mercator_to_geo', 'geo_to_utm', 'utm_to_geo', 'geo_to_ecef', 'ecef_to_geo'],
        ]

        for chain in chains:
            current_coord = boston_geographic
            for method_name in chain:
                method = getattr(transformer, method_name)
                current_coord = method(current_coord)

            # Final coordinate should be geographic and close to original
            assert isinstance(current_coord, Geographic)
            assert abs(current_coord.latitude_deg - boston_geographic.latitude_deg) < 1e-5
            assert abs(current_coord.longitude_deg - boston_geographic.longitude_deg) < 1e-5
            assert abs(current_coord.altitude_m - boston_geographic.altitude_m) < 1e-2

    def _haversine_distance(self, coord1: Geographic, coord2: Geographic) -> float:
        """Calculate haversine distance between two geographic coordinates."""
        R = 6371000  # Earth's radius in meters

        lat1_rad = math.radians(coord1.latitude_deg)
        lat2_rad = math.radians(coord2.latitude_deg)
        delta_lat = math.radians(coord2.latitude_deg - coord1.latitude_deg)
        delta_lon = math.radians(coord2.longitude_deg - coord1.longitude_deg)

        a = (math.sin(delta_lat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c
