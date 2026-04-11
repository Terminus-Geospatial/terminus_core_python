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
#    File:    test_warp_extent.py
#    Author:  Marvin Smith
#    Date:    04/10/2026
#
"""
Unit tests for Warp_Extent
"""

from tmns.geo.coord import Geographic, UTM
from tmns.geo.coord.crs import CRS
from tmns.geo.proj import Warp_Extent


class TestWarpExtent:
    """Test the Warp_Extent NamedTuple and its methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.min_geo = Geographic.create(35.0, -119.0)
        self.max_geo = Geographic.create(36.0, -118.0)
        self.corners = [
            Geographic.create(36.0, -119.0),
            Geographic.create(36.0, -118.0),
            Geographic.create(35.0, -118.0),
            Geographic.create(35.0, -119.0),
        ]
        self.extent = Warp_Extent(min_point=self.min_geo, max_point=self.max_geo, corners=self.corners)

    def test_creation(self):
        """Test Warp_Extent creation."""
        assert self.extent.min_point == self.min_geo
        assert self.extent.max_point == self.max_geo
        assert len(self.extent.corners) == 4

    def test_to_dict(self):
        """Test to_dict serialization."""
        data = self.extent.to_dict()
        assert 'min_point' in data
        assert 'max_point' in data
        assert 'corners' in data
        assert data['min_point'] == (35.0, -119.0)
        assert data['max_point'] == (36.0, -118.0)
        assert len(data['corners']) == 4

    def test_from_dict(self):
        """Test from_dict deserialization."""
        data = self.extent.to_dict()
        restored = Warp_Extent.from_dict(data)
        assert restored.min_point.latitude_deg == self.min_geo.latitude_deg
        assert restored.min_point.longitude_deg == self.min_geo.longitude_deg
        assert restored.max_point.latitude_deg == self.max_geo.latitude_deg
        assert restored.max_point.longitude_deg == self.max_geo.longitude_deg
        assert len(restored.corners) == 4

    def test_from_dict_without_corners(self):
        """Test from_dict with no corners."""
        data = {
            'min_point': (35.0, -119.0),
            'max_point': (36.0, -118.0),
            'corners': None
        }
        restored = Warp_Extent.from_dict(data)
        assert restored.min_point.latitude_deg == 35.0
        assert restored.min_point.longitude_deg == -119.0
        assert restored.max_point.latitude_deg == 36.0
        assert restored.max_point.longitude_deg == -118.0
        assert restored.corners is None

    def test_compute_output_size_wgs84(self):
        """Test compute_output_size for WGS84 CRS."""
        crs = CRS.wgs84_geographic()
        gsd = 0.1  # degrees
        width, height = self.extent.compute_output_size(crs, gsd)
        # Width: 1 degree / 0.1 = 10 pixels
        # Height: 1 degree / 0.1 = 10 pixels
        assert width == 10
        assert height == 10

    def test_compute_output_size_utm(self):
        """Test compute_output_size for UTM CRS."""
        # Create extent in UTM zone 11N (Bakersfield area)
        utm_min = UTM.create(306805.0, 3912689.5, crs=CRS.utm_zone(11, 'N'))
        utm_max = UTM.create(318803.3, 3923887.4, crs=CRS.utm_zone(11, 'N'))
        extent = Warp_Extent(
            min_point=Geographic.create(35.338802, -119.125804),
            max_point=Geographic.create(35.441959, -118.996342),
            corners=[]
        )
        crs = CRS.utm_zone(11, 'N')
        gsd = 10.0  # meters
        width, height = extent.compute_output_size(crs, gsd)
        # Width: ~12000 meters / 10 = ~1200 pixels
        # Height: ~11200 meters / 10 = ~1120 pixels
        assert width > 0
        assert height > 0
        assert width == 1199  # 11998.3 / 10 = 1199.83 → 1199
        assert height == 1119  # 11197.9 / 10 = 1119.79 → 1119

    def test_compute_output_size_small_gsd(self):
        """Test compute_output_size with small GSD (higher resolution)."""
        crs = CRS.wgs84_geographic()
        gsd = 0.01  # degrees (higher resolution)
        width, height = self.extent.compute_output_size(crs, gsd)
        # Width: 1 degree / 0.01 = 100 pixels
        # Height: 1 degree / 0.01 = 100 pixels
        assert width == 100
        assert height == 100

    def test_compute_output_size_large_gsd(self):
        """Test compute_output_size with large GSD (lower resolution)."""
        crs = CRS.wgs84_geographic()
        gsd = 1.0  # degrees (lower resolution)
        width, height = self.extent.compute_output_size(crs, gsd)
        # Width: 1 degree / 1.0 = 1 pixel
        # Height: 1 degree / 1.0 = 1 pixel
        assert width == 1
        assert height == 1

    def test_roundtrip_serialization(self):
        """Test that to_dict and from_dict roundtrip correctly."""
        original = self.extent
        data = original.to_dict()
        restored = Warp_Extent.from_dict(data)
        assert restored.min_point.latitude_deg == original.min_point.latitude_deg
        assert restored.min_point.longitude_deg == original.min_point.longitude_deg
        assert restored.max_point.latitude_deg == original.max_point.latitude_deg
        assert restored.max_point.longitude_deg == original.max_point.longitude_deg
        for i, corner in enumerate(restored.corners):
            assert corner.latitude_deg == original.corners[i].latitude_deg
            assert corner.longitude_deg == original.corners[i].longitude_deg
