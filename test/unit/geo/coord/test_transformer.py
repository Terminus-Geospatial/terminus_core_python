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
#    File:    test_transformer.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for coordinate transformation functionality.
"""

# Python Standard Libraries

# Third-Party Libraries
import pytest

from tmns.geo.coord.crs import CRS
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.geographic import Geographic

# Project Libraries
from tmns.geo.coord.transformer import Transformer
from tmns.geo.coord.ups import UPS
from tmns.geo.coord.utm import UTM
from tmns.geo.coord.web_mercator import Web_Mercator


# Fixtures for common objects
@pytest.fixture
def nyc_geographic():
    """New York City geographic coordinate."""
    return Geographic.create(40.7128, -74.0060, 10.5)

@pytest.fixture
def transformer():
    """Transformer instance."""
    return Transformer()


class Test_Transformer:
    """Test coordinate transformation functionality."""

    def test_transformer_creation(self):
        """Test creating transformer."""
        transformer = Transformer()
        assert transformer is not None

    def test_transformer_singleton(self):
        """Test transformer singleton behavior."""
        transformer1 = Transformer()
        transformer2 = Transformer()

        # Transformer should be stateless, so instances should be equivalent
        assert type(transformer1) is type(transformer2)

    def test_geographic_to_utm(self, transformer, nyc_geographic):
        """Test geographic to UTM transformation."""
        utm = transformer.transform(nyc_geographic, "EPSG:32618")

        assert isinstance(utm, UTM)
        assert utm.crs == "EPSG:32618"
        assert utm.easting_m > 0
        assert utm.northing_m > 0

    def test_utm_to_geographic(self, transformer):
        """Test UTM to geographic transformation."""
        utm = UTM.create(583000, 4507000, "EPSG:32618", 10.5)
        geo = transformer.transform(utm, "EPSG:4326")

        assert isinstance(geo, Geographic)
        assert abs(geo.latitude_deg - 40.7) < 1.0  # Within reasonable tolerance
        assert abs(geo.longitude_deg + 74.0) < 1.0  # Within reasonable tolerance

    def test_geographic_to_web_mercator(self, transformer, nyc_geographic):
        """Test geographic to Web Mercator transformation."""
        wm = transformer.transform(nyc_geographic, "EPSG:3857")

        assert isinstance(wm, Web_Mercator)
        assert wm.easting_m < 0  # NYC is in western hemisphere
        assert wm.northing_m > 0  # NYC is in northern hemisphere

    def test_web_mercator_to_geographic(self, transformer):
        """Test Web Mercator to geographic transformation."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        geo = transformer.transform(wm, "EPSG:4326")

        assert isinstance(geo, Geographic)
        assert abs(geo.latitude_deg - 40.7) < 1.0
        assert abs(geo.longitude_deg + 74.0) < 1.0

    def test_geographic_to_ecef(self, transformer, nyc_geographic):
        """Test geographic to ECEF transformation."""
        ecef = transformer.transform(nyc_geographic, "EPSG:4978")

        assert isinstance(ecef, ECEF)
        # Check that we have reasonable ECEF coordinates for NYC
        # NYC should be roughly 6,371 km from Earth center
        distance_from_center = (ecef.x_m**2 + ecef.y_m**2 + ecef.z_m**2)**0.5
        assert 6300000 < distance_from_center < 6500000  # Within reasonable Earth radius range
        assert ecef.z_m > 0  # NYC is in northern hemisphere

    def test_transform_with_crs_object(self, transformer, nyc_geographic):
        """Test transformation using CRS object instead of string."""
        target_crs = CRS.from_epsg(32618)  # UTM zone 18N
        utm = transformer.transform(nyc_geographic, target_crs)

        assert isinstance(utm, UTM)
        assert utm.crs == "EPSG:32618"
        assert utm.easting_m > 0
        assert utm.northing_m > 0

    def test_ecef_to_geographic(self, transformer):
        """Test ECEF to geographic transformation."""
        ecef = ECEF.create(-2700000, -4300000, 3850000)
        geo = transformer.transform(ecef, "EPSG:4326")

        assert isinstance(geo, Geographic)
        assert -90 <= geo.latitude_deg <= 90
        assert -180 <= geo.longitude_deg <= 180

    def test_geographic_to_ups_north(self, transformer):
        """Test geographic to UPS North transformation."""
        # North pole coordinate
        geo = Geographic.create(89.5, 0.0, 1000.0)
        ups = transformer.transform(geo, "EPSG:3413")  # UPS North

        assert isinstance(ups, UPS)
        assert ups.hemisphere == "N"

    def test_geographic_to_ups_south(self, transformer):
        """Test geographic to UPS South transformation."""
        # South pole coordinate
        geo = Geographic.create(-89.5, 180.0, 500.0)
        ups = transformer.transform(geo, "EPSG:3414")  # UPS South

        assert isinstance(ups, UPS)
        assert ups.hemisphere == "S"

    def test_ups_to_geographic(self, transformer):
        """Test UPS to geographic transformation."""
        ups_north = UPS.create(2000000.0, 2000000.0, "N", 1000.0)
        geo = transformer.transform(ups_north, "EPSG:4326")

        assert isinstance(geo, Geographic)
        assert geo.latitude_deg > 80  # Should be near north pole

    def test_same_crs_transformation(self, transformer, nyc_geographic):
        """Test transformation to same CRS."""
        result = transformer.transform(nyc_geographic, "EPSG:4326")

        assert isinstance(result, Geographic)
        assert result == nyc_geographic

    def test_invalid_target_crs(self, transformer, nyc_geographic):
        """Test transformation to invalid CRS."""
        with pytest.raises(ValueError):
            transformer.transform(nyc_geographic, "EPSG:99999")

    def test_transformation_with_altitude(self, transformer):
        """Test transformation preserving altitude."""
        geo = Geographic.create(40.7, -74.0, 100.0)
        utm = transformer.transform(geo, "EPSG:32618")

        assert utm.altitude_m == 100.0

    def test_transformation_without_altitude(self, transformer):
        """Test transformation without altitude."""
        geo = Geographic.create(40.7, -74.0)
        utm = transformer.transform(geo, "EPSG:32618")

        assert utm.altitude_m is None


    def test_transformation_chain(self, transformer):
        """Test chain of transformations."""
        geo = Geographic.create(40.7, -74.0, 10.5)

        # Geographic -> UTM -> Web Mercator -> Geographic
        utm = transformer.transform(geo, "EPSG:32618")
        wm = transformer.transform(utm, "EPSG:3857")
        geo_back = transformer.transform(wm, "EPSG:4326")

        assert isinstance(geo_back, Geographic)
        # Should be close to original (within transformation tolerance)
        assert abs(geo_back.latitude_deg - geo.latitude_deg) < 0.001
        assert abs(geo_back.longitude_deg - geo.longitude_deg) < 0.001

    def test_transformation_precision(self, transformer):
        """Test transformation precision."""
        # Use known coordinate with high precision
        geo = Geographic.create(40.712773, -74.005973, 10.5)
        utm = transformer.transform(geo, "EPSG:32618")
        geo_back = transformer.transform(utm, "EPSG:4326")

        # Should maintain high precision
        assert abs(geo_back.latitude_deg - geo.latitude_deg) < 0.000001
        assert abs(geo_back.longitude_deg - geo.longitude_deg) < 0.000001

    def test_transformation_error_handling(self, transformer):
        """Test transformation error handling."""
        # Test with invalid coordinate
        with pytest.raises(ValueError):
            transformer.transform(None, "EPSG:4326")

        # Test with invalid CRS
        invalid_geo = Geographic.create(40.7, -74.0)  # Valid coordinate
        with pytest.raises(ValueError):
            transformer.transform(invalid_geo, "EPSG:99999")  # Invalid EPSG

    def test_geo_to_utm_with_zone(self, transformer):
        """Test geo_to_utm with explicit zone parameter."""
        geo = Geographic.create(40.7, -74.0)
        utm = transformer.geo_to_utm(geo, zone=18)

        assert isinstance(utm, UTM)
        assert utm.crs == "EPSG:32618"  # UTM zone 18N

    def test_geo_to_utm_auto_zone(self, transformer):
        """Test geo_to_utm with automatic zone detection."""
        geo = Geographic.create(40.7, -74.0)
        utm = transformer.geo_to_utm(geo)

        assert isinstance(utm, UTM)
        assert utm.crs == "EPSG:32618"  # UTM zone 18N

    def test_geo_to_web_mercator_direct(self, transformer):
        """Test geo_to_web_mercator direct method."""
        geo = Geographic.create(40.7, -74.0)
        wm = transformer.geo_to_web_mercator(geo)

        assert isinstance(wm, Web_Mercator)

    def test_geo_to_ecef_direct(self, transformer):
        """Test geo_to_ecef direct method."""
        geo = Geographic.create(40.7, -74.0, 10.5)
        ecef = transformer.geo_to_ecef(geo)

        assert isinstance(ecef, ECEF)
        assert ecef.z_m > 0  # Northern hemisphere

    def test_geo_to_ecef_no_altitude(self, transformer):
        """Test geo_to_ecef without altitude."""
        geo = Geographic.create(40.7, -74.0)
        ecef = transformer.geo_to_ecef(geo)

        assert isinstance(ecef, ECEF)
        assert ecef.z_m > 0

    def test_utm_to_geo_direct(self, transformer):
        """Test utm_to_geo direct method."""
        utm = UTM.create(583000, 4507000, "EPSG:32618", 10.5)
        geo = transformer.utm_to_geo(utm)

        assert isinstance(geo, Geographic)
        assert geo.altitude_m == 10.5

    def test_web_mercator_to_geo_direct(self, transformer):
        """Test web_mercator_to_geo direct method."""
        wm = Web_Mercator.create(-8238310.24, 4969803.74, 10.5)
        geo = transformer.web_mercator_to_geo(wm)

        assert isinstance(geo, Geographic)

    def test_ecef_to_geo_direct(self, transformer):
        """Test ecef_to_geo direct method."""
        ecef = ECEF.create(-2700000, -4300000, 3850000)
        geo = transformer.ecef_to_geo(ecef)

        assert isinstance(geo, Geographic)
        assert -90 <= geo.latitude_deg <= 90
        assert -180 <= geo.longitude_deg <= 180

    def test_get_utm_zone(self, transformer):
        """Test get_utm_zone method."""
        # NYC should be in zone 18N
        crs_str = transformer.get_utm_zone(-74.0, 40.7)
        assert crs_str == "EPSG:32618"

        # Southern hemisphere - same zone number (18), different base
        crs_str = transformer.get_utm_zone(-74.0, -40.7)
        assert crs_str == "EPSG:32718"

    def test_get_epsg_info(self, transformer):
        """Test get_epsg_info method."""
        info = transformer.get_epsg_info(4326)
        assert info['code'] == 4326
        assert info['string'] == "EPSG:4326"
        assert 'coordinate_type' in info
        assert 'is_utm' in info
        assert 'is_ups' in info

    def test_get_epsg_info_from_string(self, transformer):
        """Test get_epsg_info_from_string method."""
        info = transformer.get_epsg_info_from_string("EPSG:4326")
        assert info['code'] == 4326
        assert info['string'] == "EPSG:4326"

    def test_to_utm(self, transformer):
        """Test to_utm method."""
        geo = Geographic.create(40.7, -74.0)
        utm = transformer.to_utm(geo)

        assert isinstance(utm, UTM)
        assert utm.crs == "EPSG:32618"
