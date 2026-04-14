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
    return catalog


@pytest.fixture
def manager_with_mock_sources(mock_geotiff_source):
    """Manager with mocked elevation sources."""
    sources = [mock_geotiff_source]
    return Manager(sources)


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

    @patch('pathlib.Path.rglob')
    @patch('pathlib.Path.exists')
    def test_catalog_discovery(self, mock_exists, mock_rglob):
        """Test catalog discovers GeoTIFF files."""
        mock_exists.return_value = True
        mock_rglob.return_value = [Path("file1.tif"), Path("file2.tif")]

        with patch('tmns.geo.terrain.catalog.GeoTIFF') as mock_geotiff:
            catalog = Catalog("/test/catalog")

            # Current implementation eagerly loads GeoTIFF objects during discovery
            assert mock_geotiff.call_count == 2
            assert len(catalog.source_cache) == 2

    @patch('pathlib.Path.exists')
    def test_catalog_missing_directory(self, mock_exists):
        """Test handling of missing catalog directory."""
        mock_exists.return_value = False

        catalog = Catalog("/nonexistent/catalog")
        assert len(catalog.source_cache) == 0

    def test_elevation_meters_from_sources(self, mock_geotiff_source):
        """Test getting elevation from catalog sources."""
        catalog = Catalog.__new__(Catalog)  # Create without init
        catalog.source_cache = {Path("/test.tif"): mock_geotiff_source}
        catalog.catalog_root = Path("/test")

        coord = Geographic(40.7, -74.0)
        elevation = catalog.elevation_meters(coord)

        assert elevation == 100.5
        mock_geotiff_source.elevation_meters.assert_called_once_with(coord, None)

    def test_get_sources_for_coordinate(self, mock_geotiff_source):
        """Test getting sources that contain a coordinate."""
        catalog = Catalog.__new__(Catalog)  # Create without init
        catalog.source_cache = {Path("/test.tif"): mock_geotiff_source}
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
        manager = Manager([mock_geotiff_source])

        assert len(manager.sources) == 1
        assert manager.coord_transformer is not None

    def test_manager_creation_no_sources(self):
        """Test that manager accepts empty sources list."""
        manager = Manager([])
        assert len(manager.sources) == 0

    def test_elevation_meters(self, manager_with_mock_sources, sample_geographic_coord):
        """Test getting elevation from manager."""
        elevation = manager_with_mock_sources.elevation(sample_geographic_coord)
        assert elevation == 100.5

    def test_elevation_point(self, manager_with_mock_sources, sample_geographic_coord):
        """Test getting elevation point from manager."""
        point = manager_with_mock_sources.elevation_point(sample_geographic_coord)
        assert isinstance(point, Elevation_Point)
        assert point.coord.latitude_deg == sample_geographic_coord.latitude_deg
        assert point.coord.longitude_deg == sample_geographic_coord.longitude_deg
        assert point.source == "GeoTIFF (test.tif)"
        assert point.coord.altitude_m == 100.5

    def test_elevation_meters_no_data(self, mock_geotiff_source):
        """Test handling when no elevation data is available."""
        mock_geotiff_source.elevation_meters.return_value = None

        manager = Manager([mock_geotiff_source])
        elevation = manager.elevation(Geographic(40.7, -74.0))
        assert elevation is None

    def test_coordinate_conversion_in_elevation(self, manager_with_mock_sources):
        """Test that coordinates are properly converted for elevation queries."""
        elevation = manager_with_mock_sources.elevation(Geographic(40.7, -74.0))
        assert elevation == 100.5

    def test_source_failure_falls_through(self, mock_geotiff_source):
        """Test that a failing source is skipped and next source is tried."""
        failing_source = Mock(spec=GeoTIFF)
        failing_source.name = "Failing Source"
        failing_source.elevation_meters.side_effect = RuntimeError("I/O error")
        failing_source.vertical_datum = ELIPSOIDAL_DATUM

        manager = Manager([failing_source, mock_geotiff_source])
        elevation = manager.elevation(Geographic(40.7, -74.0))
        assert elevation == 100.5

    def test_get_info(self, manager_with_mock_sources):
        """Test get_info returns manager configuration."""
        info = manager_with_mock_sources.get_info()
        assert 'sources' in info
        assert 'num_sources' in info
        assert 'interpolation' in info
        assert info['num_sources'] == 1

    def test_no_cache_attributes(self, manager_with_mock_sources):
        """Verify cache-related attributes and methods no longer exist."""
        manager = manager_with_mock_sources
        assert not hasattr(manager, 'cache_enabled')
        assert not hasattr(manager, 'elevation_cache')
        assert not hasattr(manager, 'cache_file')
        assert not hasattr(manager, 'clear_cache')
        assert not hasattr(manager, 'get_cache_stats')


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
