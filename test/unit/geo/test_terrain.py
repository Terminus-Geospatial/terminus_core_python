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
from rasterio.transform import Affine

# Project Libraries
from tmns.geo.coord import Geographic, UTM, UPS, Web_Mercator, ECEF, Transformer
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
    source.get_elevations.return_value = [100.5, 200.0, 300.0]  # Match 3 coordinates
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

        ups = point.to_ups()
        assert isinstance(ups, UPS)

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

    @patch('rasterio.open')
    def test_local_dem_creation(self, mock_rasterio_open):
        """Test creating local DEM source."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.bounds = Mock(left=0, right=1000, bottom=0, top=1000)
        mock_dataset.transform = Affine.identity()
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        source = Local_DEM_Elevation_Source("test.tif")

        assert source.name == "Local DEM (test.tif)"
        assert source.dataset == mock_dataset
        assert source.epsg_code == 4326

    @patch('rasterio.open')
    def test_local_dem_file_not_found(self, mock_rasterio_open):
        """Test handling of missing DEM file."""
        mock_rasterio_open.side_effect = FileNotFoundError("File not found")

        with pytest.raises(RuntimeError):
            Local_DEM_Elevation_Source("nonexistent.tif")

    @patch('rasterio.open')
    def test_get_elevation(self, mock_rasterio_open):
        """Test getting elevation from local DEM."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.bounds = Mock(left=0, right=1000, bottom=0, top=1000)
        mock_dataset.transform = Affine.identity()
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_dataset.read.return_value = np.array([[100.5]])
        mock_dataset.nodata = None
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        source = Local_DEM_Elevation_Source("test.tif")

        # Test elevation query
        elevation = source.get_elevation(40.7, -74.0)
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

    @patch('rasterio.open')
    def test_geotiff_creation(self, mock_rasterio_open):
        """Test creating GeoTIFF source."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.bounds = Mock(left=-74.1, right=-73.9, bottom=40.6, top=40.8)
        mock_dataset.transform = Affine.identity()
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        source = GeoTIFF_Elevation_Source("test.tif")

        assert source.name == "GeoTIFF (test.tif)"
        assert source.dataset == mock_dataset
        assert source.epsg_code == 4326

    @patch('rasterio.open')
    def test_contains_coordinate(self, mock_rasterio_open):
        """Test coordinate containment check."""
        # Mock rasterio dataset with NYC bounds
        mock_dataset = Mock()
        mock_dataset.bounds = Mock(left=-74.1, right=-73.9, bottom=40.6, top=40.8)
        mock_dataset.transform = Affine.identity()
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        source = GeoTIFF_Elevation_Source("test.tif")

        # Test coordinate inside bounds
        coord_inside = Geographic(40.7, -74.0)
        assert source.contains(coord_inside) == True

        # Test coordinate outside bounds
        coord_outside = Geographic(0.0, 0.0)
        assert source.contains(coord_outside) == False

    @patch('rasterio.open')
    def test_get_elevation(self, mock_rasterio_open):
        """Test getting elevation from GeoTIFF."""
        # Mock rasterio dataset
        mock_dataset = Mock()
        mock_dataset.bounds = Mock(left=-74.1, right=-73.9, bottom=40.6, top=40.8)
        mock_dataset.transform = Affine.identity()
        mock_dataset.crs = Mock()
        mock_dataset.crs.to_epsg.return_value = 4326
        mock_dataset.read.return_value = np.array([[100.5]])
        mock_dataset.nodata = None
        mock_rasterio_open.return_value.__enter__.return_value = mock_dataset

        source = GeoTIFF_Elevation_Source("test.tif")

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
        assert point.coord == coord
        assert point.source == "GeoTIFF (test.tif)"
        assert point.coord.altitude_m == 100.5

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
        assert all(e == 100.5 for e in elevations)  # Mock returns same value

    def test_coordinate_conversion_in_elevation(self, manager_with_mock_sources):
        """Test that coordinates are properly converted for elevation queries."""
        manager = manager_with_mock_sources

        # Test with different coordinate types
        utm_coord = UTM(583000, 4507000, "EPSG:32618", 10.5)
        elevation = manager.elevation(utm_coord)

        # Should still work (coordinate gets converted to geographic)
        assert elevation == 100.5

    def test_cache_operations(self, manager_with_mock_sources, sample_geographic_coord):
        """Test cache operations."""
        manager = Manager([mock_geotiff_source()], cache_enabled=True)
        coord = sample_geographic_coord

        # First call should populate cache
        elevation1 = manager.elevation(coord)

        # Second call should use cache
        elevation2 = manager.elevation(coord)

        assert elevation1 == elevation2
        assert len(manager.elevation_cache) > 0

    def test_clear_cache(self, manager_with_mock_sources):
        """Test clearing cache."""
        manager = Manager([mock_geotiff_source()], cache_enabled=True)
        coord = Geographic(40.7, -74.0)

        # Add something to cache
        manager.elevation(coord)
        assert len(manager.elevation_cache) > 0

        # Clear cache
        manager.clear_cache()
        assert len(manager.elevation_cache) == 0

    def test_get_cache_stats(self, manager_with_mock_sources):
        """Test getting cache statistics."""
        manager = Manager([mock_geotiff_source()], cache_enabled=True)
        coord = Geographic(40.7, -74.0)

        # Add something to cache
        manager.elevation(coord)

        stats = manager.get_cache_stats()
        assert 'cached_points' in stats
        assert 'cache_file' in stats
        assert 'sources' in stats
        assert stats['cached_points'] > 0


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
        mock_manager_class.assert_called_once_with([mock_source], cache_enabled=True)

    @patch('tmns.geo.terrain.Terrain_Catalog')
    @patch('tmns.geo.terrain.Manager')
    def test_create_catalog_manager(self, mock_manager_class, mock_catalog_class):
        """Test creating catalog manager."""
        mock_catalog = Mock()
        mock_catalog.sources = [Mock()]
        mock_catalog_class.return_value = mock_catalog
        mock_manager = Mock()
        mock_manager_class.return_value = mock_manager

        manager = create_catalog_manager("/test/catalog", cache_enabled=True)

        assert manager == mock_manager
        mock_catalog_class.assert_called_once_with("/test/catalog")
        mock_manager_class.assert_called_once_with([mock_catalog], cache_enabled=True)

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
