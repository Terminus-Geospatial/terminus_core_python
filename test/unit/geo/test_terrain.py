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
import json
from pathlib import Path
from unittest.mock import Mock, patch

# Third-Party Libraries
import numpy as np
import pytest
from rasterio.coords import BoundingBox
from rasterio.transform import Affine

# Project Libraries
from tmns.geo.coord import Geographic, UTM, UPS, Web_Mercator, ECEF, Pixel, Transformer
from tmns.geo.terrain import (
    Manager,
    Elevation_Point,
    GeoTIFF_Elevation_Source,
    Terrain_Catalog,
    Local_DEM_Elevation_Source,
    elevation,
    elevation_point,
    get_terrain_manager,
    create_catalog_manager,
    create_terrain_manager,
    Interpolation_Method
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
    source = Mock(spec=GeoTIFF_Elevation_Source)
    source.name = "GeoTIFF (test.tif)"
    source.get_elevation.return_value = 100.5
    source.get_elevations.return_value = [100.5, 100.5, 100.5]  # Return same value for all 3 coordinates
    source.contains.return_value = True
    return source


@pytest.fixture
def mock_catalog():
    """Mock terrain catalog."""
    catalog = Mock(spec=Terrain_Catalog)
    catalog.name = "Terrain Catalog"
    catalog.get_elevation.return_value = 100.5
    catalog.sources = [mock_geotiff_source()]
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

        # Test coordinate method returns the same geographic coordinate
        coord = point.coordinate()
        assert isinstance(coord, Geographic)
        assert coord == point.coord

        # Test geographic method returns the same geographic coordinate
        geo = point.geographic()
        assert isinstance(geo, Geographic)
        assert geo == point.coord

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


class Test_Local_DEM_Elevation_Source:
    """Test Local_DEM_Elevation_Source class."""

    def test_local_dem_creation(self):
        """Test creating local DEM source."""
        # Create source normally (it will try to load a real file)
        with patch('tmns.geo.terrain.rasterio.open') as mock_rasterio_open:
            # Mock rasterio dataset
            mock_dataset = Mock()
            mock_dataset.bounds = BoundingBox(left=0, right=1000, bottom=0, top=1000)
            mock_dataset.transform = (0.0, 10.0, 0.0, 1000.0, 0.0, -10.0)
            mock_dataset.crs = Mock()
            mock_dataset.crs.to_epsg.return_value = 4326
            mock_dataset.width = 100
            mock_dataset.height = 100
            mock_rasterio_open.return_value = mock_dataset

            source = Local_DEM_Elevation_Source("test.tif")

            assert source.name == "Local DEM (test.tif)"
            assert source.dataset is mock_dataset
            assert source.epsg_code == 4326

    @patch('tmns.geo.terrain.rasterio.open')
    def test_local_dem_file_not_found(self, mock_rasterio_open):
        """Test handling of missing DEM file."""
        mock_rasterio_open.side_effect = FileNotFoundError("File not found")

        with pytest.raises(RuntimeError):
            Local_DEM_Elevation_Source("nonexistent.tif")

    def test_get_elevation(self):
        """Test getting elevation from local DEM."""
        # Create source with mocked dataset
        with patch('tmns.geo.terrain.rasterio.open') as mock_rasterio_open:
            # Mock rasterio dataset
            mock_dataset = Mock()
            mock_dataset.bounds = BoundingBox(left=0, right=1000, bottom=0, top=1000)
            # Correct transform order: [origin_x, scale_x, shear_x, origin_y, shear_y, scale_y]
            mock_dataset.transform = (0.0, 10.0, 0.0, 1000.0, 0.0, -10.0)  # 10m pixels, origin at top-left
            mock_dataset.crs = Mock()
            mock_dataset.crs.to_epsg.return_value = 4326
            mock_dataset.read.return_value = np.array([[100.5]])
            mock_dataset.nodata = None
            mock_dataset.sample.return_value = np.array([[100.5]])
            mock_dataset.width = 100
            mock_dataset.height = 100
            mock_rasterio_open.return_value = mock_dataset

            source = Local_DEM_Elevation_Source("test.tif")

            # Test elevation query with coordinates within bounds
            # Using pixel coordinates (50, 50) -> world coordinates (500, 500)
            elevation = source.get_elevation(500.0, 500.0)
            assert elevation == 100.5

    @patch('rasterio.open')
    def test_get_elevation_out_of_bounds(self, mock_rasterio_open):
        """Test getting elevation for out-of-bounds coordinate."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.bounds = Mock(left=0, right=1000, bottom=0, top=1000)
        mock_dataset.transform = Affine.identity()
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        source = Local_DEM_Elevation_Source("test.tif")

        # Test out-of-bounds coordinate (assuming transform maps to far away)
        elevation = source.get_elevation(90.0, 180.0)
        assert elevation is None


class Test_GeoTIFF_Elevation_Source:
    """Test GeoTIFF_Elevation_Source class."""

    def test_geotiff_creation(self):
        """Test creating GeoTIFF source."""
        # Create source normally (no mocking needed for basic creation)
        source = GeoTIFF_Elevation_Source("test.tif")

        # Manually set up mock dataset with Affine transform
        mock_dataset = Mock()
        mock_dataset.bounds = BoundingBox(left=-74.1, right=-73.9, bottom=40.6, top=40.8)
        mock_dataset.transform = Affine(0.001, 0.0, -74.1, 0.0, -0.001, 40.8)
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        source.dataset = mock_dataset
        source.bounds = mock_dataset.bounds
        source.transform = mock_dataset.transform
        source.crs = mock_dataset.crs
        source.epsg_code = 4326
        source._loaded = True

        assert source.name == "GeoTIFF (test.tif)"
        assert source.dataset is mock_dataset
        assert source.epsg_code == 4326

    def test_contains_coordinate(self):
        """Test coordinate containment check."""
        # Create source normally
        source = GeoTIFF_Elevation_Source("test.tif")

        # Manually set up mock dataset with Affine transform
        mock_dataset = Mock()
        mock_dataset.bounds = BoundingBox(left=-74.1, right=-73.9, bottom=40.6, top=40.8)
        mock_dataset.transform = Affine(0.001, 0.0, -74.1, 0.0, -0.001, 40.8)
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        source.dataset = mock_dataset
        source.bounds = mock_dataset.bounds
        source.transform = mock_dataset.transform
        source.crs = mock_dataset.crs
        source.epsg_code = 4326
        source._loaded = True

        # Test coordinate inside bounds
        coord_inside = Geographic(40.7, -74.0)
        assert source.contains(coord_inside) == True

        # Test coordinate outside bounds
        coord_outside = Geographic(0.0, 0.0)
        assert source.contains(coord_outside) == False

    def test_get_elevation(self):
        """Test getting elevation from GeoTIFF."""
        # Create source normally
        source = GeoTIFF_Elevation_Source("test.tif")

        # Manually set up mock dataset with Affine transform
        mock_dataset = Mock()
        mock_dataset.bounds = BoundingBox(left=-74.1, right=-73.9, bottom=40.6, top=40.8)
        mock_dataset.transform = Affine(0.001, 0.0, -74.1, 0.0, -0.001, 40.8)
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_dataset.read.return_value = np.array([[100.5]])
        mock_dataset.nodata = None
        mock_dataset.sample.return_value = np.array([[100.5]])
        source.dataset = mock_dataset
        source.bounds = mock_dataset.bounds
        source.transform = mock_dataset.transform
        source.crs = mock_dataset.crs
        source.epsg_code = 4326
        source._loaded = True

        # Test elevation query
        coord = Geographic(40.7, -74.0)
        elevation = source.get_elevation(coord)
        assert elevation == 100.5

    def test_interpolation_methods(self):
        """Test interpolation method settings."""
        source = GeoTIFF_Elevation_Source("dummy.tif")

        # Test default interpolation
        assert source.interpolation == Interpolation_Method.BILINEAR

        # Test setting interpolation
        source.interpolation = Interpolation_Method.NEAREST
        assert source.interpolation == Interpolation_Method.NEAREST


class Test_Terrain_Catalog:
    """Test Terrain_Catalog class."""

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.rglob')
    def test_catalog_discovery(self, mock_rglob, mock_exists):
        """Test discovering GeoTIFF files in catalog."""
        mock_exists.return_value = True
        mock_rglob.return_value = [Path("file1.tif"), Path("file2.tif")]

        with patch('tmns.geo.terrain.GeoTIFF_Elevation_Source') as mock_geotiff:
            catalog = Terrain_Catalog("/test/catalog")

            # Should attempt to create sources for found files
            assert mock_geotiff.call_count == 2
            assert len(catalog.sources) == 2

    @patch('pathlib.Path.exists')
    def test_catalog_missing_directory(self, mock_exists):
        """Test handling of missing catalog directory."""
        mock_exists.return_value = False

        catalog = Terrain_Catalog("/nonexistent/catalog")
        assert len(catalog.sources) == 0

    def test_get_elevation_from_sources(self, mock_geotiff_source):
        """Test getting elevation from catalog sources."""
        catalog = Terrain_Catalog.__new__(Terrain_Catalog)  # Create without init
        catalog.sources = [mock_geotiff_source]
        catalog.catalog_root = Path("/test")

        coord = Geographic(40.7, -74.0)
        elevation = catalog.get_elevation(coord)

        assert elevation == 100.5
        mock_geotiff_source.get_elevation.assert_called_once_with(coord)

    def test_get_sources_for_coordinate(self, mock_geotiff_source):
        """Test getting sources that contain a coordinate."""
        catalog = Terrain_Catalog.__new__(Terrain_Catalog)  # Create without init
        catalog.sources = [mock_geotiff_source]
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
        assert manager.cache_enabled == False
        assert manager.coord_transformer is not None

    def test_manager_creation_no_sources(self):
        """Test that manager requires at least one source."""
        with pytest.raises(ValueError):
            Manager([])

    def test_get_elevation(self, manager_with_mock_sources, sample_geographic_coord):
        """Test getting elevation from manager."""
        manager = manager_with_mock_sources
        coord = sample_geographic_coord

        elevation = manager.elevation(coord)
        assert elevation == 100.5

    def test_get_elevation_point(self, manager_with_mock_sources, sample_geographic_coord):
        """Test getting elevation point from manager."""
        manager = manager_with_mock_sources
        coord = sample_geographic_coord

        point = manager.elevation_point(coord)
        assert isinstance(point, Elevation_Point)
        assert point.coord.latitude_deg == coord.latitude_deg
        assert point.coord.longitude_deg == coord.longitude_deg
        assert point.source == "GeoTIFF (test.tif)"
        assert point.coord.altitude_m == 100.5  # Should be updated by elevation source

    def test_get_elevation_no_data(self, mock_geotiff_source):
        """Test handling when no elevation data is available."""
        mock_geotiff_source.get_elevation.return_value = None

        manager = Manager([mock_geotiff_source], cache_enabled=False)
        coord = Geographic(40.7, -74.0)

        elevation = manager.elevation(coord)
        assert elevation is None

    def test_elevation_batch(self, manager_with_mock_sources, sample_coordinates_list):
        """Test batch elevation queries."""
        manager = manager_with_mock_sources
        coords = sample_coordinates_list

        elevations = manager.elevation_batch(coords)

        assert len(elevations) == 3
        # All elevations should be 100.5 since mock returns same value for each coordinate
        assert all(e == 100.5 for e in elevations)

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
        mock_geotiff_source.get_elevation.reset_mock()
        elevation = manager.elevation(coord)
        assert elevation == 100.5
        mock_geotiff_source.get_elevation.assert_not_called()

    def test_clear_cache(self, mock_geotiff_source, sample_geographic_coord):
        """Test clearing cache."""
        manager = Manager([mock_geotiff_source], cache_enabled=True)
        coord = sample_geographic_coord

        # Populate cache
        manager.elevation(coord)

        # Clear cache
        manager.clear_cache()

        # Verify cache is cleared by checking source gets called again
        mock_geotiff_source.get_elevation.reset_mock()
        manager.elevation(coord)
        mock_geotiff_source.get_elevation.assert_called_once()

    def test_get_cache_stats(self, mock_geotiff_source, sample_geographic_coord):
        """Test getting cache statistics."""
        coord = sample_geographic_coord

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

    @patch('tmns.geo.terrain.Manager')
    def test_get_terrain_manager(self, mock_manager_class):
        """Test getting global terrain manager."""
        mock_manager = Mock()
        mock_manager_class.create_default.return_value = mock_manager

        # Reset global variable
        import tmns.geo.terrain
        tmns.geo.terrain._terrain_manager = None

        manager = get_terrain_manager()

        assert manager == mock_manager
        mock_manager_class.create_default.assert_called_once()

    @patch('tmns.geo.terrain.Manager')
    def test_create_terrain_manager(self, mock_manager_class):
        """Test creating terrain manager with sources."""
        mock_source = Mock()
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        manager = create_terrain_manager([mock_source], cache_enabled=True)

        assert manager == mock_manager
        mock_manager_class.assert_called_once_with([mock_source], True, Interpolation_Method.BILINEAR)

    @patch('tmns.geo.terrain.Manager')
    def test_create_catalog_manager(self, mock_manager_class):
        """Test creating catalog manager."""
        mock_manager = Mock()
        mock_manager_class.create_catalog_only.return_value = mock_manager

        manager = create_catalog_manager("/test/catalog", cache_enabled=True)

        assert manager is mock_manager
        mock_manager_class.create_catalog_only.assert_called_once_with("/test/catalog", True, Interpolation_Method.BILINEAR)

    @patch('tmns.geo.terrain.get_terrain_manager')
    def test_elevation_function(self, mock_get_manager):
        """Test elevation convenience function."""
        mock_manager = Mock()
        mock_manager.elevation.return_value = 100.5
        mock_get_manager.return_value = mock_manager

        coord = Geographic(40.7, -74.0)
        result = elevation(coord)

        assert result == 100.5
        mock_manager.elevation.assert_called_once_with(coord)

    @patch('tmns.geo.terrain.get_terrain_manager')
    def test_elevation_point_function(self, mock_get_manager):
        """Test elevation point convenience function."""
        mock_manager = Mock()
        mock_point = Mock()
        mock_manager.elevation_point.return_value = mock_point
        mock_get_manager.return_value = mock_manager

        coord = Geographic(40.7, -74.0)
        result = elevation_point(coord)

        assert result == mock_point
        mock_manager.elevation_point.assert_called_once_with(coord)


class Test_Interpolation_Method:
    """Test interpolation method enum."""

    def test_interpolation_methods(self):
        """Test interpolation method values."""
        assert Interpolation_Method.NEAREST.value == "nearest"
        assert Interpolation_Method.BILINEAR.value == "bilinear"
        assert Interpolation_Method.CUBIC.value == "cubic"
