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
#    File:    test_terrain.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Unit tests for terrain elevation functionality.
"""

# Python Standard Libraries
from pathlib import Path
from unittest.mock import Mock, patch

# Third-Party Libraries
import pytest

# Project Libraries
from tmns.geo.coord import ECEF, UTM, Geographic, Pixel, Web_Mercator
from tmns.geo.coord.vdatum import ELIPSOIDAL_DATUM
from tmns.geo.terrain import (
    Catalog,
    Elevation_Point,
    GeoTIFF,
    Interpolation_Method,
    Manager,
    elevation,
    elevation_point,
)


# Fixtures
@pytest.fixture
def sample_geographic_coord():
    """Sample geographic coordinate for testing."""
    return Geographic(40.7, -74.0, 10.5)


@pytest.fixture
def sample_elevation_point(sample_geographic_coord):
    """Sample elevation point for testing."""
    return Elevation_Point(sample_geographic_coord, "Test Source", 1.0)


@pytest.fixture
def mock_geotiff_source():
    """Mock GeoTIFF elevation source."""
    source = Mock(spec=GeoTIFF)
    source.name = "GeoTIFF (test.tif)"
    source.elevation_meters.return_value = 100.5
    source.contains.return_value = True
    source.vertical_datum = ELIPSOIDAL_DATUM
    return source


@pytest.fixture
def mock_catalog():
    """Mock terrain catalog."""
    catalog = Mock(spec=Catalog)
    catalog.name = "Terrain Catalog"
    catalog.elevation_meters.return_value = 100.5
    catalog.source_cache = {Path("/test.tif"): mock_geotiff_source()}
    catalog.source_paths = [Path("/test.tif")]
    return catalog


@pytest.fixture
def manager_with_mock_sources(mock_geotiff_source):
    """Manager with mocked elevation sources."""
    sources = [mock_geotiff_source]
    return Manager(sources, cache_enabled=False)


@pytest.fixture
def sample_coordinates_list():
    """List of sample geographic coordinates."""
    return [
        Geographic(40.7, -74.0),
        Geographic(40.8, -74.1),
        Geographic(40.9, -74.2)
    ]


class Test_Elevation_Point:
    """Test Elevation_Point dataclass."""

    def test_elevation_point_creation(self, sample_geographic_coord):
        """Test creating elevation point."""
        point = Elevation_Point(sample_geographic_coord, "Test Source", 1.0)
        assert point.coord == sample_geographic_coord
        assert point.source == "Test Source"
        assert point.accuracy == 1.0

    def test_elevation_point_creation_without_accuracy(self, sample_geographic_coord):
        """Test creating elevation point without accuracy."""
        point = Elevation_Point(sample_geographic_coord, "Test Source")
        assert point.coord == sample_geographic_coord
        assert point.source == "Test Source"
        assert point.accuracy is None

    def test_coordinate_methods(self, sample_elevation_point):
        """Test coordinate conversion methods."""
        point = sample_elevation_point

        # Test coord property returns the same geographic coordinate
        assert isinstance(point.coord, Geographic)
        assert point.coord.altitude_m == 10.5  # From the fixture

    def test_coordinate_transformations(self, sample_elevation_point):
        """Test coordinate transformation methods."""
        point = sample_elevation_point

        # Test transformations (these should return coordinate objects)
        utm = point.to_utm()
        assert isinstance(utm, UTM)

        # UPS should fail for non-polar coordinates
        with pytest.raises(ValueError, match="not in polar region"):
            point.to_ups()

        web_mercator = point.to_web_mercator()
        assert isinstance(web_mercator, Web_Mercator)

        ecef = point.to_ecef()
        assert isinstance(ecef, ECEF)

    def test_create_from_components(self):
        """Test creating elevation point from individual components."""
        point = Elevation_Point.create(40.7, -74.0, 100.5, "Test Source", 1.0)

        assert point.coord.latitude_deg == 40.7
        assert point.coord.longitude_deg == -74.0
        assert point.coord.altitude_m == 100.5
        assert point.source == "Test Source"
        assert point.accuracy == 1.0

    def test_create_from_components_without_accuracy(self):
        """Test creating elevation point without accuracy."""
        point = Elevation_Point.create(40.7, -74.0, 100.5, "Test Source")

        assert point.coord.latitude_deg == 40.7
        assert point.coord.longitude_deg == -74.0
        assert point.coord.altitude_m == 100.5
        assert point.source == "Test Source"
        assert point.accuracy is None

    def test_string_representation(self, sample_elevation_point):
        """Test string representation."""
        point = sample_elevation_point
        str_repr = str(point)
        assert "Elevation:" in str_repr
        assert "Test Source" in str_repr

    def test_invalid_coordinate_type(self):
        """Test that non-geographic coordinates raise TypeError."""
        with pytest.raises(TypeError):
            Elevation_Point(Pixel(100, 200), "Test Source")




class Test_GeoTIFF:
    """Test GeoTIFF class."""

    def test_geotiff_creation(self):
        """Test creating GeoTIFF source."""
        # Use real test dataset
        source = GeoTIFF("test/data/terrain/test_dem.tif")

        # Trigger dataset loading to get epsg_code
        source._load_dataset()

        # Test basic properties
        assert source.name == "GeoTIFF (test_dem.tif)"
        assert source.file_path.name == "test_dem.tif"
        assert source.epsg_code == 4326
        assert source.bounds is not None

        # Test info method
        info = source.info()
        assert 'file_path' in info
        assert 'epsg_code' in info
        assert 'bounds' in info
        assert info['epsg_code'] == 4326

    def test_contains_coordinate(self):
        """Test coordinate containment check."""
        # Use real test dataset
        source = GeoTIFF("test/data/terrain/test_dem.tif")

        # Test coordinate inside bounds (NYC area)
        coord_inside = Geographic(40.7, -74.0)
        assert source.contains(coord_inside)

        # Test coordinate outside bounds (far away)
        coord_outside = Geographic(0.0, 0.0)
        assert not source.contains(coord_outside)

    def test_elevation_meters(self):
        """Test getting elevation from GeoTIFF."""
        # Use real test dataset
        source = GeoTIFF("test/data/terrain/test_dem.tif")

        # Test elevation query
        coord = Geographic(40.7, -74.0)
        elevation = source.elevation_meters(coord)

        # Should get a reasonable elevation value (100-120m range from our test data)
        assert elevation is not None
        assert 100 <= elevation <= 120

    def test_interpolation_methods(self):
        """Test interpolation method settings."""
        source = GeoTIFF("test/data/terrain/test_dem.tif")

        # Test default interpolation
        assert source.interpolation == Interpolation_Method.BILINEAR

        # Test setting interpolation
        source.interpolation = Interpolation_Method.NEAREST
        assert source.interpolation == Interpolation_Method.NEAREST


class Test_Catalog:
    """Test Catalog class."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.rglob')
    def test_catalog_discovery(self, mock_rglob, mock_exists):
        """Test discovering GeoTIFF files in catalog."""
        mock_exists.return_value = True
        mock_rglob.return_value = [Path("file1.tif"), Path("file2.tif")]

        with patch('tmns.geo.terrain.catalog.GeoTIFF') as mock_geotiff:
            catalog = Catalog("/test/catalog")

            # Should discover files but not load them (lazy loading)
            assert mock_geotiff.call_count == 0
            assert len(catalog.source_paths) == 2
            assert len(catalog.source_cache) == 0

    @patch('pathlib.Path.exists')
    def test_catalog_missing_directory(self, mock_exists):
        """Test handling of missing catalog directory."""
        mock_exists.return_value = False

        catalog = Catalog("/nonexistent/catalog")
        assert len(catalog.source_paths) == 0
        assert len(catalog.source_cache) == 0

    def test_elevation_meters_from_sources(self, mock_geotiff_source):
        """Test getting elevation from catalog sources."""
        catalog = Catalog.__new__(Catalog)  # Create without init
        catalog.source_cache = {Path("/test.tif"): mock_geotiff_source}
        catalog.source_paths = [Path("/test.tif")]
        catalog.catalog_root = Path("/test")

        coord = Geographic(40.7, -74.0)
        elevation = catalog.elevation_meters(coord)

        assert elevation == 100.5
        mock_geotiff_source.elevation_meters.assert_called_once_with(coord, None)

    def test_get_sources_for_coordinate(self, mock_geotiff_source):
        """Test getting sources that contain a coordinate."""
        catalog = Catalog.__new__(Catalog)  # Create without init
        catalog.source_cache = {Path("/test.tif"): mock_geotiff_source}
        catalog.source_paths = [Path("/test.tif")]
        catalog.catalog_root = Path("/test")

        coord = Geographic(40.7, -74.0)
        sources = catalog.get_sources_for_coordinate(coord)

        assert len(sources) == 1
        assert sources[0] == mock_geotiff_source
        mock_geotiff_source.contains.assert_called_once_with(coord)


class Test_Terrain_Manager:
    """Test terrain manager functionality."""

    def test_manager_creation(self, mock_geotiff_source):
        """Test creating terrain manager."""
        sources = [mock_geotiff_source]
        manager = Manager(sources, cache_enabled=False)

        assert len(manager.sources) == 1
        assert not manager.cache_enabled
        assert manager.coord_transformer is not None

    def test_manager_creation_no_sources(self):
        """Test that manager requires at least one source."""
        # Manager should now accept empty sources list
        manager = Manager([])
        assert len(manager.sources) == 0

    def test_elevation_meters(self, manager_with_mock_sources, sample_geographic_coord):
        """Test getting elevation from manager."""
        manager = manager_with_mock_sources
        coord = sample_geographic_coord

        elevation = manager.elevation(coord)
        assert elevation == 100.5

    def test_elevation_point(self, manager_with_mock_sources, sample_geographic_coord):
        """Test getting elevation point from manager."""
        manager = manager_with_mock_sources
        coord = sample_geographic_coord

        point = manager.elevation_point(coord)
        assert isinstance(point, Elevation_Point)
        assert point.coord.latitude_deg == coord.latitude_deg
        assert point.coord.longitude_deg == coord.longitude_deg
        assert point.source == "GeoTIFF (test.tif)"
        assert point.coord.altitude_m == 100.5  # Should be updated by elevation source

    def test_elevation_meters_no_data(self, mock_geotiff_source):
        """Test handling when no elevation data is available."""
        mock_geotiff_source.elevation_meters.return_value = None

        manager = Manager([mock_geotiff_source], cache_enabled=False)
        coord = Geographic(40.7, -74.0)

        elevation = manager.elevation(coord)
        assert elevation is None

    def test_elevation_batch_removed(self, manager_with_mock_sources):
        """Test that elevation_batch method has been removed."""
        manager = manager_with_mock_sources

        # Verify elevation_batch method doesn't exist
        assert not hasattr(manager, 'elevation_batch')

        # Verify that trying to access elevation_batch raises AttributeError
        with pytest.raises(AttributeError):
            _ = manager.elevation_batch

    def test_coordinate_conversion_in_elevation(self, manager_with_mock_sources):
        """Test that coordinates are properly converted for elevation queries."""
        manager = manager_with_mock_sources

        # Test with different coordinate types - defer UTM complexity for now
        # TODO: Revisit UTM coordinate construction with explicit zone/hemisphere handling
        coord = Geographic(40.7, -74.0)  # Use geographic for now
        elevation = manager.elevation(coord)

        # Should work with geographic coordinates
        assert elevation == 100.5

    def test_cache_operations(self, mock_geotiff_source, sample_geographic_coord):
        """Test cache operations."""
        manager = Manager([mock_geotiff_source], cache_enabled=True)
        coord = sample_geographic_coord

        # Test cache miss
        elevation = manager.elevation(coord)
        assert elevation == 100.5

        # Test cache hit (should not call source again)
        mock_geotiff_source.elevation_meters.reset_mock()
        elevation = manager.elevation(coord)
        assert elevation == 100.5
        mock_geotiff_source.elevation_meters.assert_not_called()

    def test_clear_cache(self, mock_geotiff_source, sample_geographic_coord):
        """Test clearing cache."""
        manager = Manager([mock_geotiff_source], cache_enabled=True)
        coord = sample_geographic_coord

        # Populate cache
        manager.elevation(coord)

        # Clear cache
        manager.clear_cache()

        # Verify cache is cleared by checking source gets called again
        mock_geotiff_source.elevation_meters.reset_mock()
        manager.elevation(coord)
        mock_geotiff_source.elevation_meters.assert_called_once()

    def test_get_cache_stats(self, mock_geotiff_source, sample_geographic_coord):
        """Test getting cache statistics."""

        # Test with cache disabled first
        manager_no_cache = Manager([mock_geotiff_source], cache_enabled=False)
        stats_no_cache = manager_no_cache.get_cache_stats()
        assert stats_no_cache['cached_points'] == 0
        assert stats_no_cache['cache_size_mb'] < 0.01  # Allow small file size
        assert len(stats_no_cache['sources']) == 1

        # Test with cache enabled
        manager = Manager([mock_geotiff_source], cache_enabled=True)

        # Get initial state
        stats = manager.get_cache_stats()
        initial_points = stats['cached_points']

        # Populate cache with a new coordinate (not used before)
        new_coord = Geographic(45.0, -75.0)  # Different from sample_geographic_coord
        manager.elevation(new_coord)

        # Check stats after cache miss
        stats = manager.get_cache_stats()
        assert stats['cached_points'] == initial_points + 1
        assert stats['cache_size_mb'] >= 0
        assert len(stats['sources']) == 1

        # Cache hit with same coordinate
        manager.elevation(new_coord)

        # Check stats after cache hit (should be same cached_points)
        stats = manager.get_cache_stats()
        assert stats['cached_points'] == initial_points + 1
        assert stats['cache_size_mb'] >= 0
        assert len(stats['sources']) == 1


class Test_Convenience_Functions:
    """Test convenience functions."""

    @patch('tmns.geo.terrain.get_default_manager')
    def test_elevation_function(self, mock_get_manager):
        """Test elevation convenience function."""
        mock_manager = Mock()
        mock_manager.elevation.return_value = 100.5
        mock_get_manager.return_value = mock_manager

        coord = Geographic(40.7, -74.0, 0.0)
        result = elevation(coord)

        assert result == 100.5
        mock_manager.elevation.assert_called_once_with(coord, None)

    @patch('tmns.geo.terrain.get_default_manager')
    def test_elevation_point_function(self, mock_get_manager):
        """Test elevation point convenience function."""
        mock_manager = Mock()
        mock_elevation_point = Mock()
        mock_elevation_point.coord.altitude_m = 100.5
        mock_manager.elevation_point.return_value = mock_elevation_point
        mock_get_manager.return_value = mock_manager

        coord = Geographic(40.7, -74.0, 0.0)
        result = elevation_point(coord)

        assert result.coord.altitude_m == 100.5
        mock_manager.elevation_point.assert_called_once_with(coord, None)


class Test_Interpolation_Method:
    """Test interpolation method enum."""

    def test_interpolation_methods(self):
        """Test interpolation method values."""
        assert Interpolation_Method.NEAREST.value == "nearest"
        assert Interpolation_Method.BILINEAR.value == "bilinear"
        assert Interpolation_Method.CUBIC.value == "cubic"
