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
#    File:    test_web_mercator.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for Web Mercator coordinate functionality.
"""

# Python Standard Libraries

# Third-Party Libraries
import pytest

from tmns.geo.coord.types import Type

# Project Libraries
from tmns.geo.coord.web_mercator import Web_Mercator


# Fixtures for common objects
@pytest.fixture
def web_mercator_coordinate():
    """Web Mercator coordinate."""
    return Web_Mercator.create(-8238310.24, 4969803.74, 10.5)

@pytest.fixture
def web_mercator_bounds():
    """Web Mercator world bounds."""
    return Web_Mercator.world_bounds()


class Test_Web_Mercator_Constants:
    """Test Web Mercator constants."""

    def test_constants_exist(self):
        """Test that all constants are defined."""
        assert Web_Mercator.MIN_BOUND == -20037508.342789244
        assert Web_Mercator.MAX_BOUND == 20037508.342789244
        assert Web_Mercator.WORLD_WIDTH_M == 40075016.68557849
        assert Web_Mercator.BASE_TILE_SIZE == 256

    def test_constants_relationships(self):
        """Test mathematical relationships between constants."""
        # World width should be twice the max bound
        assert Web_Mercator.WORLD_WIDTH_M == 2 * Web_Mercator.MAX_BOUND
        assert Web_Mercator.WORLD_WIDTH_M == -2 * Web_Mercator.MIN_BOUND

    def test_constants_in_bounds(self):
        """Test that bounds constants work correctly."""
        # Point at min bound should be in bounds
        wm_min = Web_Mercator.create(Web_Mercator.MIN_BOUND, Web_Mercator.MIN_BOUND, 0.0)
        assert wm_min.is_in_bounds()

        # Point at max bound should be in bounds
        wm_max = Web_Mercator.create(Web_Mercator.MAX_BOUND, Web_Mercator.MAX_BOUND, 0.0)
        assert wm_max.is_in_bounds()

        # Point just outside bounds should fail
        wm_outside = Web_Mercator.create(Web_Mercator.MAX_BOUND + 1.0, Web_Mercator.MAX_BOUND + 1.0, 0.0)
        assert not wm_outside.is_in_bounds()


class Test_Web_Mercator_Meters_Per_Pixel:
    """Test Web Mercator meters per pixel calculations."""

    @pytest.mark.parametrize("zoom_level,expected_mpp", [
        (0, Web_Mercator.WORLD_WIDTH_M / Web_Mercator.BASE_TILE_SIZE),  # World in one tile
        (1, Web_Mercator.WORLD_WIDTH_M / (Web_Mercator.BASE_TILE_SIZE * 2)),  # 2x2 tiles
        (10, Web_Mercator.WORLD_WIDTH_M / (Web_Mercator.BASE_TILE_SIZE * 1024)),  # 1024x1024 tiles
        (18, Web_Mercator.WORLD_WIDTH_M / (Web_Mercator.BASE_TILE_SIZE * 262144)),  # High zoom
    ])
    def test_meters_per_pixel_values(self, web_mercator_coordinate, zoom_level, expected_mpp):
        """Test meters per pixel at various zoom levels."""
        mpp = web_mercator_coordinate.meters_per_pixel(zoom_level)
        assert abs(mpp - expected_mpp) < 1e-10

    def test_meters_per_pixel_halving(self, web_mercator_coordinate):
        """Test that meters per pixel halves each zoom level."""
        mpp_z0 = web_mercator_coordinate.meters_per_pixel(0)
        mpp_z1 = web_mercator_coordinate.meters_per_pixel(1)
        mpp_z2 = web_mercator_coordinate.meters_per_pixel(2)

        # Each zoom level should halve the meters per pixel
        assert abs(mpp_z1 - mpp_z0 / 2) < 1e-10
        assert abs(mpp_z2 - mpp_z1 / 2) < 1e-10


class Test_Web_Mercator_Tile_Coordinates:
    """Test Web Mercator tile coordinate calculations."""

    def test_tile_coordinates_range(self, web_mercator_coordinate):
        """Test tile coordinates are within expected range."""
        for zoom in range(0, 5):  # Test low zoom levels
            tile_x, tile_y = web_mercator_coordinate.tile_coordinates(zoom)
            max_tile = 2 ** zoom
            assert 0 <= tile_x < max_tile
            assert 0 <= tile_y < max_tile

    def test_tile_coordinates_consistency(self, web_mercator_coordinate):
        """Test tile coordinate consistency."""
        # Same zoom should give same result
        tile1 = web_mercator_coordinate.tile_coordinates(10)
        tile2 = web_mercator_coordinate.tile_coordinates(10)
        assert tile1 == tile2

    def test_world_center_tile_coordinates(self):
        """Test tile coordinates at world center."""
        # World center in Web Mercator
        wm_center = Web_Mercator.create(0.0, 0.0, 0.0)

        # At zoom level 0, world center should be tile (0, 0)
        tile_x, tile_y = wm_center.tile_coordinates(0)
        assert tile_x == 0
        assert tile_y == 0


class Test_Web_Mercator_API_Integration:
    """Test Web Mercator API integration."""

    def test_bounds_type(self):
        """Test that world_bounds returns correct type."""
        Web_Mercator.world_bounds()

    def test_coordinate_type(self, web_mercator_coordinate):
        """Test coordinate type identification."""
        assert web_mercator_coordinate.type() == Type.WEB_MERCATOR

    def test_coordinate_arithmetic(self):
        """Test coordinate arithmetic operations."""
        wm1 = Web_Mercator.create(1000.0, 2000.0, 100.0)
        wm2 = Web_Mercator.create(500.0, 1000.0, 50.0)

        # Test subtraction
        result = wm1 - wm2
        assert isinstance(result, Web_Mercator)
        assert result.easting_m == 500.0
        assert result.northing_m == 1000.0
        assert result.altitude_m == 100.0

    def test_coordinate_equality(self):
        """Test coordinate equality."""
        wm1 = Web_Mercator.create(1000.0, 2000.0, 100.0)
        wm2 = Web_Mercator.create(1000.0, 2000.0, 100.0)
        wm3 = Web_Mercator.create(1000.1, 2000.0, 100.0)

        assert wm1 == wm2
        assert wm1 != wm3

    def test_coordinate_copy(self, web_mercator_coordinate):
        """Test coordinate copying."""
        wm_copy = web_mercator_coordinate.copy()

        assert web_mercator_coordinate == wm_copy
        assert web_mercator_coordinate is not wm_copy
        assert web_mercator_coordinate.crs == wm_copy.crs


class Test_Web_Mercator_Coordinate:
    """Test Web Mercator coordinate class."""

    @pytest.mark.parametrize("easting,northing,alt", [
        (-8238310.24, 4969803.74, 10.5),
        (0.0, 0.0, None),
        (1113194.91, 1113194.91, 100.0),
        (Web_Mercator.MIN_BOUND, Web_Mercator.MAX_BOUND, 0.0),  # World bounds
    ])
    def test_web_mercator_creation(self, easting, northing, alt):
        """Test creating Web Mercator coordinates."""
        wm = Web_Mercator.create(easting, northing, alt)

        assert wm.easting_m == easting
        assert wm.northing_m == northing
        if alt is None:
            assert wm.altitude_m is None
        else:
            assert wm.altitude_m == alt

    def test_web_mercator_creation_with_altitude(self):
        """Test creating Web Mercator coordinates with altitude."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        assert wm.altitude_m == 10.5

    def test_web_mercator_creation_without_altitude(self):
        """Test creating Web Mercator coordinates without altitude."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74)
        assert wm.altitude_m is None

    def test_web_mercator_bounds_validation(self):
        """Test Web Mercator coordinate bounds validation."""
        # Valid coordinates (within world bounds)
        Web_Mercator.create(Web_Mercator.MIN_BOUND, Web_Mercator.MAX_BOUND)  # Top-left
        Web_Mercator.create(Web_Mercator.MAX_BOUND, Web_Mercator.MIN_BOUND)  # Bottom-right

        # Test bounds checking
        valid_coord = Web_Mercator.create(0.0, 0.0, 0.0)
        assert valid_coord.is_in_bounds()

        invalid_coord = Web_Mercator.create(Web_Mercator.MAX_BOUND + 1000.0, 0.0, 0.0)
        assert not invalid_coord.is_in_bounds()

    def test_web_mercator_equality(self):
        """Test Web Mercator coordinate equality."""
        wm1 = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        wm2 = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        wm3 = Web_Mercator.create(-8238310.25, 4969803.74, 10.5)  # Different easting

        assert wm1 == wm2
        assert wm1 != wm3

    def test_web_mercator_hash(self):
        """Test Web Mercator coordinate hashing."""
        wm1 = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        wm2 = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)

        assert hash(wm1) == hash(wm2)

    def test_web_mercator_string_representation(self):
        """Test Web Mercator coordinate string representation."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        str_repr = str(wm)

        assert "-8238310.24" in str_repr
        assert "4969803.74" in str_repr
        assert "10.5" in str_repr

    def test_web_mercator_type(self):
        """Test Web Mercator coordinate type."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        assert wm.type() == Type.WEB_MERCATOR

    def test_web_mercator_copy(self):
        """Test Web Mercator coordinate copying."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        wm_copy = wm.copy()

        assert wm == wm_copy
        assert wm is not wm_copy

    def test_web_mercator_world_bounds(self, web_mercator_bounds):
        """Test Web Mercator world bounds."""
        assert web_mercator_bounds.min_easting == Web_Mercator.MIN_BOUND
        assert web_mercator_bounds.min_northing == Web_Mercator.MIN_BOUND
        assert web_mercator_bounds.max_easting == Web_Mercator.MAX_BOUND
        assert web_mercator_bounds.max_northing == Web_Mercator.MAX_BOUND

    def test_web_mercator_is_in_bounds(self, web_mercator_coordinate):
        """Test Web Mercator bounds checking."""
        assert web_mercator_coordinate.is_in_bounds()

        # Test out of bounds
        out_of_bounds = Web_Mercator.create(Web_Mercator.MIN_BOUND - 1.0, 0.0)
        assert not out_of_bounds.is_in_bounds()

    def test_web_mercator_meters_per_pixel(self, web_mercator_coordinate):
        """Test Web Mercator meters per pixel calculation."""
        # At zoom level 0, one pixel is about 156543 meters
        meters_per_pixel = web_mercator_coordinate.meters_per_pixel(0)
        assert abs(meters_per_pixel - 156543.03) < 1.0

    def test_web_mercator_tile_coordinates(self, web_mercator_coordinate):
        """Test Web Mercator tile coordinate calculation."""
        tile_x, tile_y = web_mercator_coordinate.tile_coordinates(10)  # Zoom level 10

        assert isinstance(tile_x, int)
        assert isinstance(tile_y, int)
        assert 0 <= tile_x < 2**10
        assert 0 <= tile_y < 2**10

    def test_web_mercator_pixel_coordinates(self, web_mercator_coordinate):
        """Test Web Mercator pixel coordinates."""
        # Test pixel coordinates at zoom level 10
        pixel_x, pixel_y = web_mercator_coordinate.pixel_coordinates(10)
        assert isinstance(pixel_x, int)
        assert isinstance(pixel_y, int)
        assert 0 <= pixel_x < Web_Mercator.BASE_TILE_SIZE
        assert 0 <= pixel_y < Web_Mercator.BASE_TILE_SIZE

        # Test with custom tile size
        pixel_x_512, pixel_y_512 = web_mercator_coordinate.pixel_coordinates(10, 512)
        assert isinstance(pixel_x_512, int)
        assert isinstance(pixel_y_512, int)
        assert 0 <= pixel_x_512 < 512
        assert 0 <= pixel_y_512 < 512

        # Test default tile size constant
        pixel_x_default, pixel_y_default = web_mercator_coordinate.pixel_coordinates(10, Web_Mercator.BASE_TILE_SIZE)
        assert pixel_x_default == pixel_x
        assert pixel_y_default == pixel_y
