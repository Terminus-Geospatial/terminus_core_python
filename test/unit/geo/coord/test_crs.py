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
#    File:    test_crs.py
#    Author:  Marvin Smith
#    Date:    04/07/2026
#
"""Unit tests for CRS (Coordinate Reference System) class."""

import pytest

# Project Libraries
from tmns.geo.coord.crs import CRS
from tmns.geo.coord.epsg import Code


class Test_CRS_Creation:
    """Test CRS creation methods."""

    def test_crs_from_epsg_valid(self):
        """Test creating CRS from valid EPSG code."""
        crs = CRS.from_epsg(4326)
        assert crs.epsg_code == 4326
        assert str(crs) == "CRS(EPSG:4326)"
        assert repr(crs) == "CRS(epsg_code=4326)"

    def test_crs_from_epsg_invalid_type(self):
        """Test creating CRS with invalid EPSG type."""
        with pytest.raises(TypeError, match="EPSG code must be an integer"):
            CRS.from_epsg("4326")

    def test_crs_from_epsg_invalid_value(self):
        """Test creating CRS with invalid EPSG value."""
        with pytest.raises(ValueError, match="EPSG code must be positive"):
            CRS.from_epsg(0)

        with pytest.raises(ValueError, match="EPSG code must be positive"):
            CRS.from_epsg(-1)

    def test_crs_utm_zone_northern(self):
        """Test creating UTM zone CRS for northern hemisphere."""
        crs = CRS.utm_zone(10, 'N')
        assert crs.epsg_code == 32610
        assert crs.is_utm_zone()
        assert not crs.is_geographic()
        assert crs.is_projected()

    def test_crs_utm_zone_southern(self):
        """Test creating UTM zone CRS for southern hemisphere."""
        crs = CRS.utm_zone(15, 'S')
        assert crs.epsg_code == 32715
        assert crs.is_utm_zone()
        assert not crs.is_geographic()
        assert crs.is_projected()

    def test_crs_utm_zone_invalid_zone(self):
        """Test creating UTM zone with invalid zone number."""
        with pytest.raises(ValueError, match="UTM zone must be 1-60"):
            CRS.utm_zone(0, 'N')

        with pytest.raises(ValueError, match="UTM zone must be 1-60"):
            CRS.utm_zone(61, 'N')

    def test_crs_utm_zone_invalid_hemisphere(self):
        """Test creating UTM zone with invalid hemisphere."""
        with pytest.raises(ValueError, match="Hemisphere must be 'N' or 'S'"):
            CRS.utm_zone(10, 'E')

        with pytest.raises(ValueError, match="Hemisphere must be 'N' or 'S'"):
            CRS.utm_zone(10, 'n')  # Case sensitive

    def test_crs_web_mercator(self):
        """Test creating Web Mercator CRS."""
        crs = CRS.web_mercator()
        assert crs.epsg_code == Code.WEB_MERCATOR
        assert crs.is_projected()
        assert not crs.is_geographic()
        assert not crs.is_utm_zone()

    def test_crs_ecef(self):
        """Test creating ECEF CRS."""
        crs = CRS.ecef()
        assert crs.epsg_code == Code.ECEF
        assert not crs.is_geographic()
        assert not crs.is_projected()
        assert not crs.is_utm_zone()

    def test_crs_wgs84(self):
        """Test creating WGS84 geographic CRS."""
        crs = CRS.wgs84_geographic()
        assert crs.epsg_code == Code.WGS84
        assert crs.is_geographic()
        assert not crs.is_projected()
        assert not crs.is_utm_zone()


class Test_CRS_Comparison:
    """Test CRS comparison methods."""

    def test_crs_equality_same(self):
        """Test equality of identical CRS objects."""
        crs1 = CRS.from_epsg(4326)
        crs2 = CRS.from_epsg(4326)
        assert crs1 == crs2
        assert not (crs1 != crs2)

    def test_crs_equality_different(self):
        """Test inequality of different CRS objects."""
        crs1 = CRS.from_epsg(4326)
        crs2 = CRS.from_epsg(3857)
        assert crs1 != crs2
        assert not (crs1 == crs2)

    def test_crs_equality_non_crs(self):
        """Test equality with non-CRS objects."""
        crs = CRS.from_epsg(4326)
        assert crs != "CRS(EPSG:4326)"
        assert crs != 4326
        assert crs != None

    def test_crs_hash(self):
        """Test CRS hash functionality."""
        crs1 = CRS.from_epsg(4326)
        crs2 = CRS.from_epsg(4326)
        crs3 = CRS.from_epsg(3857)

        # Same EPSG codes should have same hash
        assert hash(crs1) == hash(crs2)

        # Different EPSG codes should have different hashes
        assert hash(crs1) != hash(crs3)

        # CRS should be hashable (usable in sets and as dict keys)
        crs_set = {crs1, crs2, crs3}
        assert len(crs_set) == 2  # crs1 and crs2 are duplicates

    def test_crs_dict_key(self):
        """Test using CRS as dictionary key."""
        crs_dict = {}
        crs1 = CRS.from_epsg(4326)
        crs2 = CRS.from_epsg(3857)

        crs_dict[crs1] = "WGS84"
        crs_dict[crs2] = "Web Mercator"

        assert crs_dict[crs1] == "WGS84"
        assert crs_dict[crs2] == "Web Mercator"
        assert len(crs_dict) == 2


class Test_CRS_Properties:
    """Test CRS property access."""

    def test_crs_lazy_loading(self):
        """Test that CRS definition is lazy-loaded."""
        crs = CRS.from_epsg(4326)

        # Initially, definition should not be loaded
        assert crs._definition is None

        # Access definition to trigger lazy loading
        definition = crs.definition
        assert definition is not None
        assert crs._definition is definition  # Should be cached

    def test_crs_properties(self):
        """Test CRS property access."""
        crs = CRS.from_epsg(4326)

        # These should work without errors (actual values depend on EPSG database)
        assert crs.coordinate_type is not None
        assert crs.unit is not None
        assert crs.projection is not None

    def test_crs_horizontal_datum(self):
        """Test horizontal datum property."""
        crs = CRS.from_epsg(4326)
        datum = crs.horizontal_datum
        assert datum is not None

    def test_crs_vertical_datum(self):
        """Test vertical datum property."""
        crs = CRS.from_epsg(4326)
        # May return None if no vertical datum is defined
        vertical_datum = crs.vertical_datum
        # No assertion - just ensure it doesn't raise error


class Test_CRS_Utility_Methods:
    """Test CRS utility methods."""

    @pytest.mark.parametrize("epsg_code,expected_geographic", [
        (4326, True),   # WGS84
        (3857, False),  # Web Mercator
        (32610, False), # UTM Zone 10N
        (4978, False),  # ECEF
    ])
    def test_crs_is_geographic(self, epsg_code, expected_geographic):
        """Test geographic CRS detection."""
        crs = CRS.from_epsg(epsg_code)
        assert crs.is_geographic() == expected_geographic

    @pytest.mark.parametrize("epsg_code,expected_projected", [
        (4326, False),  # WGS84
        (3857, True),   # Web Mercator
        (32610, True),  # UTM Zone 10N
        (4978, False),  # ECEF
    ])
    def test_crs_is_projected(self, epsg_code, expected_projected):
        """Test projected CRS detection."""
        crs = CRS.from_epsg(epsg_code)
        assert crs.is_projected() == expected_projected

    @pytest.mark.parametrize("epsg_code,expected_utm", [
        (4326, False),   # WGS84
        (3857, False),   # Web Mercator
        (32610, True),   # UTM Zone 10N
        (32715, True),   # UTM Zone 15S
        (4978, False),   # ECEF
    ])
    def test_crs_is_utm_zone(self, epsg_code, expected_utm):
        """Test UTM zone CRS detection."""
        crs = CRS.from_epsg(epsg_code)
        assert crs.is_utm_zone() == expected_utm

    def test_crs_get_utm_zone_info_northern(self):
        """Test UTM zone info extraction for northern hemisphere."""
        crs = CRS.from_epsg(32610)  # UTM Zone 10N
        zone, hemisphere = crs.get_utm_zone_info()
        assert zone == 10
        assert hemisphere == 'N'

    def test_crs_get_utm_zone_info_southern(self):
        """Test UTM zone info extraction for southern hemisphere."""
        crs = CRS.from_epsg(32715)  # UTM Zone 15S
        zone, hemisphere = crs.get_utm_zone_info()
        assert zone == 15
        assert hemisphere == 'S'

    def test_crs_get_utm_zone_info_non_utm(self):
        """Test UTM zone info extraction for non-UTM CRS."""
        crs = CRS.from_epsg(4326)  # WGS84
        with pytest.raises(ValueError, match="is not a UTM zone"):
            crs.get_utm_zone_info()

    def test_crs_get_utm_zone_info_invalid_epsg(self):
        """Test UTM zone info extraction with invalid EPSG code."""
        crs = CRS.from_epsg(9999)  # Invalid UTM EPSG code
        with pytest.raises(ValueError, match="is not a UTM zone"):
            crs.get_utm_zone_info()


class Test_CRS_Edge_Cases:
    """Test CRS edge cases and error conditions."""

    def test_crs_copy_behavior(self):
        """Test CRS copying behavior."""
        crs = CRS.from_epsg(4326)

        # Test the copy method
        crs_copy = crs.copy()

        assert crs == crs_copy
        assert crs is not crs_copy  # Different objects
        assert crs.epsg_code == crs_copy.epsg_code

    def test_crs_string_representations(self):
        """Test CRS string representations."""
        crs = CRS.from_epsg(4326)

        # Test __str__
        str_repr = str(crs)
        assert "EPSG:4326" in str_repr
        assert "CRS" in str_repr

        # Test __repr__
        repr_str = repr(crs)
        assert "epsg_code=4326" in repr_str
        assert "CRS" in repr_str

    def test_crs_large_epsg_codes(self):
        """Test CRS with large EPSG codes."""
        # Some real-world EPSG codes are quite large
        large_epsg = 32667  # UTM Zone 67N (hypothetical)
        crs = CRS.from_epsg(large_epsg)
        assert crs.epsg_code == large_epsg

    def test_crs_boundary_values(self):
        """Test CRS with boundary values."""
        # Minimum valid EPSG code
        crs = CRS.from_epsg(1)
        assert crs.epsg_code == 1

        # Test a common EPSG code range
        for epsg in [4326, 3857, 32610, 32715, 4978]:
            crs = CRS.from_epsg(epsg)
            assert crs.epsg_code == epsg
