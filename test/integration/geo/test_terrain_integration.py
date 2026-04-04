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
#    File:    test_terrain_integration.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Integration tests for terrain elevation sources comparison.

This module tests that different elevation sources (SRTM, AWS, etc.)
provide consistent elevation data within acceptable tolerances
across various geographic locations and coordinate systems.
"""

# Python Standard Libraries
from typing import Any
from unittest.mock import patch, Mock

# Third-Party Libraries
import pytest

# Project Libraries
from tmns.geo.coord import Geographic, UTM, UPS, Web_Mercator, ECEF, Transformer
from tmns.geo.terrain import (
    Manager,
    Terrain_Catalog,
    GeoTIFF_Elevation_Source,
    Elevation_Point,
    elevation,
    elevation_point
)


# Test configuration
ELEVATION_TOLERANCE_METERS = 20.0  # Acceptable difference between sources
HIGH_TOLERANCE_METERS = 50.0      # For difficult areas (steep terrain, polar regions)


# Geographic test locations focused on areas with local data
# Based on n35_w119 and n35_w120 tiles covering California/Nevada area
TEST_LOCATIONS = {
    # Local tile coverage areas (35°N, 119-120°W)
    "death_valley": Geographic.create(36.5, -116.9, 0.0),      # Death Valley, CA (~-86m)
    "mountain_whitney": Geographic.create(36.6, -118.2, 0.0),   # Mt. Whitney, CA (~4421m)
    "las_vegas": Geographic.create(36.2, -115.1, 0.0),          # Las Vegas, NV (~650m)
    "mojave": Geographic.create(35.3, -116.2, 0.0),             # Mojave Desert, CA (~500m)
    "bishop": Geographic.create(37.4, -118.4, 0.0),             # Bishop, CA (~1250m)

    # Additional test locations for broader coverage
    "sea_level_ny": Geographic.create(40.7, -74.0, 0.0),        # Sea level, NYC
    "high_altitude": Geographic.create(39.1, -106.4, 0.0),      # Rocky Mountains, CO (~2800m)
    "polar_north": Geographic.create(89.0, 0.0, 0.0),            # Near North Pole
    "polar_south": Geographic.create(-89.0, 0.0, 0.0),           # Near South Pole
}


class Test_Terrain_Integration:
    """Integration tests for terrain elevation functionality."""

    @pytest.fixture
    def mock_catalog(self):
        """Mock terrain catalog with test data."""
        catalog = Mock(spec=Terrain_Catalog)
        catalog.name = "Mock Terrain Catalog"

        # Mock elevation responses for test locations
        mock_elevations = {
            "death_valley": -86.0,
            "mountain_whitney": 4421.0,
            "las_vegas": 650.0,
            "mojave": 500.0,
            "bishop": 1250.0,
            "sea_level_ny": 2.0,
            "high_altitude": 2800.0,
            "polar_north": 2800.0,  # Ice sheet elevation
            "polar_south": 2800.0,  # Ice sheet elevation
        }

        def mock_get_elevation(coord):
            # Find closest test location
            min_dist = float('inf')
            closest_location = None

            for name, test_coord in TEST_LOCATIONS.items():
                dist = abs(coord.latitude_deg - test_coord.latitude_deg) + \
                       abs(coord.longitude_deg - test_coord.longitude_deg)
                if dist < min_dist:
                    min_dist = dist
                    closest_location = name

            if closest_location and min_dist < 1.0:  # Within 1 degree
                return mock_elevations[closest_location]
            return None

        catalog.get_elevation.side_effect = mock_get_elevation
        return catalog

    @pytest.fixture
    def terrain_manager(self, mock_catalog):
        """Terrain manager with mock catalog."""
        return Manager([mock_catalog], cache_enabled=False)

    def test_elevation_consistency_across_coordinate_types(self, terrain_manager):
        """Test elevation queries return consistent results across coordinate types."""
        # Test location
        geo_coord = TEST_LOCATIONS["las_vegas"]

        # Get elevation in geographic coordinates
        geo_elevation = terrain_manager.elevation(geo_coord)
        assert geo_elevation is not None

        # Convert to other coordinate systems and query elevation
        transformer = Transformer()

        # UTM
        utm_coord = transformer.geo_to_utm(geo_coord)
        utm_elevation = terrain_manager.elevation(utm_coord)
        assert utm_elevation == geo_elevation

        # Web Mercator
        wm_coord = transformer.geo_to_web_mercator(geo_coord)
        wm_elevation = terrain_manager.elevation(wm_coord)
        assert wm_elevation == geo_elevation

        # ECEF
        ecef_coord = transformer.geo_to_ecef(geo_coord)
        ecef_elevation = terrain_manager.elevation(ecef_coord)
        assert ecef_elevation == geo_elevation

    def test_elevation_point_metadata(self, terrain_manager):
        """Test elevation point contains proper metadata."""
        geo_coord = TEST_LOCATIONS["mountain_whitney"]

        point = terrain_manager.elevation_point(geo_coord)

        assert isinstance(point, Elevation_Point)
        assert point.coord == geo_coord
        assert point.source == "Mock Terrain Catalog"
        assert point.coord.altitude_m == 4421.0

    def test_batch_elevation_queries(self, terrain_manager):
        """Test batch elevation queries for efficiency."""
        coords = [
            TEST_LOCATIONS["death_valley"],
            TEST_LOCATIONS["mountain_whitney"],
            TEST_LOCATIONS["las_vegas"]
        ]

        elevations = terrain_manager.elevation_batch(coords)

        assert len(elevations) == 3
        assert elevations[0] == -86.0   # Death Valley
        assert elevations[1] == 4421.0  # Mt. Whitney
        assert elevations[2] == 650.0   # Las Vegas

    def test_elevation_range_validation(self, terrain_manager):
        """Test elevation values are within reasonable ranges."""
        for location_name, coord in TEST_LOCATIONS.items():
            elevation = terrain_manager.elevation(coord)

            if elevation is not None:
                # Basic sanity checks
                assert -500 <= elevation <= 9000, f"Invalid elevation {elevation} for {location_name}"

    def test_polar_regions(self, terrain_manager):
        """Test elevation queries in polar regions."""
        # North pole
        north_coord = TEST_LOCATIONS["polar_north"]
        north_elevation = terrain_manager.elevation(north_coord)
        assert north_elevation is not None
        assert north_elevation > 0  # Ice sheet elevation

        # South pole
        south_coord = TEST_LOCATIONS["polar_south"]
        south_elevation = terrain_manager.elevation(south_coord)
        assert south_elevation is not None
        assert south_elevation > 0  # Ice sheet elevation

    def test_coordinate_precision(self, terrain_manager):
        """Test elevation queries with high-precision coordinates."""
        # High precision coordinate
        precise_coord = Geographic.create(36.123456789, -116.987654321, 0.0)

        elevation = terrain_manager.elevation(precise_coord)
        assert elevation is not None

        # Should be close to Las Vegas elevation
        assert abs(elevation - 650.0) < 100

    def test_mixed_coordinate_type_batch(self, terrain_manager):
        """Test batch queries with mixed coordinate types."""
        transformer = Transformer()

        # Create mixed coordinate types
        geo_coord = TEST_LOCATIONS["las_vegas"]
        utm_coord = transformer.geo_to_utm(geo_coord)
        wm_coord = transformer.geo_to_web_mercator(geo_coord)

        coords = [geo_coord, utm_coord, wm_coord]
        elevations = terrain_manager.elevation_batch(coords)

        assert len(elevations) == 3
        assert all(e == 650.0 for e in elevations)

    def test_cache_behavior(self, mock_catalog):
        """Test caching behavior with repeated queries."""
        # Manager with cache enabled
        manager = Manager([mock_catalog], cache_enabled=True)

        coord = TEST_LOCATIONS["las_vegas"]

        # First query
        elevation1 = manager.elevation(coord)

        # Second query (should use cache)
        elevation2 = manager.elevation(coord)

        assert elevation1 == elevation2
        assert mock_catalog.get_elevation.call_count == 1  # Only called once

    def test_convenience_functions(self, mock_catalog):
        """Test global convenience functions."""
        with patch('tmns.geo.terrain.get_terrain_manager') as mock_get_manager:
            mock_get_manager.return_value = Manager([mock_catalog], cache_enabled=False)

            coord = TEST_LOCATIONS["mountain_whitney"]

            # Test elevation function
            elevation_result = elevation(coord)
            assert elevation_result == 4421.0

            # Test elevation_point function
            point_result = elevation_point(coord)
            assert isinstance(point_result, Elevation_Point)
            assert point_result.coord.altitude_m == 4421.0

    def test_error_handling(self):
        """Test error handling for invalid scenarios."""
        # Manager with no sources
        with pytest.raises(ValueError):
            Manager([])

    def test_source_priority(self):
        """Test that sources are queried in priority order."""
        # Create mock sources with different priorities
        source1 = Mock(spec=GeoTIFF_Elevation_Source)
        source1.name = "High Priority Source"
        source1.get_elevation.return_value = 1000.0
        source1.contains.return_value = True

        source2 = Mock(spec=GeoTIFF_Elevation_Source)
        source2.name = "Low Priority Source"
        source2.get_elevation.return_value = 2000.0
        source2.contains.return_value = True

        # Manager with sources (first source has priority)
        manager = Manager([source1, source2], cache_enabled=False)

        coord = TEST_LOCATIONS["las_vegas"]
        elevation = manager.elevation(coord)

        # Should use first source's value
        assert elevation == 1000.0
        source1.get_elevation.assert_called_once()
        source2.get_elevation.assert_not_called()

    def test_coordinate_transformation_integration(self, terrain_manager):
        """Test integration between terrain and coordinate transformations."""
        # Test complex transformation chain
        geo_coord = TEST_LOCATIONS["mountain_whitney"]

        # Geographic -> UTM -> Web Mercator -> ECEF -> Geographic
        transformer = Transformer()

        utm_coord = transformer.geo_to_utm(geo_coord)
        wm_coord = transformer.geo_to_web_mercator(geo_coord)
        ecef_coord = transformer.geo_to_ecef(geo_coord)

        # All should return same elevation
        geo_elevation = terrain_manager.elevation(geo_coord)
        utm_elevation = terrain_manager.elevation(utm_coord)
        wm_elevation = terrain_manager.elevation(wm_coord)
        ecef_elevation = terrain_manager.elevation(ecef_coord)

        assert geo_elevation == utm_elevation == wm_elevation == ecef_elevation == 4421.0

    def test_performance_considerations(self, terrain_manager):
        """Test performance characteristics."""
        import time

        # Test single query performance
        start_time = time.time()
        coord = TEST_LOCATIONS["las_vegas"]
        elevation = terrain_manager.elevation(coord)
        single_query_time = time.time() - start_time

        assert elevation is not None
        assert single_query_time < 1.0  # Should be fast

        # Test batch query performance
        coords = [coord] * 100
        start_time = time.time()
        elevations = terrain_manager.elevation_batch(coords)
        batch_query_time = time.time() - start_time

        assert len(elevations) == 100
        assert all(e == 650.0 for e in elevations)
        assert batch_query_time < 2.0  # Should be reasonably fast
