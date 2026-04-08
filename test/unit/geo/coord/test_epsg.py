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
#    File:    test_epsg.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for EPSG code management functionality.
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import numpy as np
import pytest

# Project Libraries
from tmns.geo.coord.epsg import Manager, Code


class Test_EPSG_Manager:
    """Test EPSG code management functionality."""

    def test_epsg_constants(self):
        """Test EPSG code constants."""
        assert Code.WGS84.value == 4326
        assert Code.WEB_MERCATOR.value == 3857
        assert Code.UTM_NORTH_BASE.value == 32600
        assert Code.UTM_SOUTH_BASE.value == 32700

    def test_manager_singleton(self):
        """Test Manager singleton pattern."""
        manager1 = Manager.global_instance()
        manager2 = Manager.global_instance()

        assert manager1 is manager2

    def test_epsg_code_creation(self):
        """Test creating EPSG code objects."""
        # Test with integer
        code1 = Code(4326)
        assert code1.value == 4326

        # Test with Code object
        code3 = Code(Code.WGS84)
        assert code3.value == 4326

    def test_epsg_code_equality(self):
        """Test EPSG code equality."""
        code1 = Code(4326)
        code2 = Code(4326)
        code3 = Code(3857)

        assert code1 == code2
        assert code1 != code3

    def test_epsg_code_hash(self):
        """Test EPSG code hashing."""
        code1 = Code(4326)
        code2 = Code(4326)

        assert hash(code1) == hash(code2)

    def test_epsg_code_string_representation(self):
        """Test EPSG code string representation."""
        code = Code(4326)
        str_repr = str(code)

        assert "4326" in str_repr

    def test_epsg_code_properties(self):
        """Test EPSG code properties."""
        code = Code(4326)

        assert code.epsg_code == 4326
        assert code.to_epsg_string() == "EPSG:4326"

    def test_is_utm_zone_north(self):
        """Test UTM north zone detection."""
        assert Code.is_utm_zone(32618)  # Zone 18N
        assert Code.is_utm_zone(32601)  # Zone 1N
        # Both north and south are UTM zones
        assert Code.is_utm_zone(32718)  # Zone 18S (also UTM)
        assert not Code.is_utm_zone(4326)  # WGS84

    def test_is_utm_zone_south(self):
        """Test UTM south zone detection."""
        assert Code.is_utm_zone(32718)  # Zone 18S
        assert Code.is_utm_zone(32701)  # Zone 1S
        # Both north and south are UTM zones
        assert Code.is_utm_zone(32618)  # Zone 18N (also UTM)
        assert not Code.is_utm_zone(4326)  # WGS84

    def test_get_utm_zone_number(self):
        """Test UTM zone number extraction."""
        zone_north_code = Code.create_utm(18, northern=True)
        zone_south_code = Code.create_utm(18, northern=False)

        zone_num_north, _ = Code.parse_utm_zone(zone_north_code)
        zone_num_south, _ = Code.parse_utm_zone(zone_south_code)

        assert zone_num_north == 18
        assert zone_num_south == 18

    def test_get_utm_hemisphere(self):
        """Test UTM hemisphere extraction."""
        zone_north_code = Code.create_utm(18, northern=True)
        zone_south_code = Code.create_utm(18, northern=False)

        _, north_hem = Code.parse_utm_zone(zone_north_code)
        _, south_hem = Code.parse_utm_zone(zone_south_code)

        assert north_hem == True
        assert south_hem == False

    def test_is_web_mercator(self):
        """Test Web Mercator detection."""
        assert Code.is_projected(3857)
        assert not Code.is_projected(4326)
        assert Code.is_projected(32618)  # UTM is projected

    def test_is_geographic(self):
        """Test geographic CRS detection."""
        assert Code.is_geographic(4326)
        assert not Code.is_geographic(3857)
        assert not Code.is_geographic(32618)

    def test_epsg_code_validation(self):
        """Test EPSG code validation."""
        # Valid EPSG codes
        Code(4326)  # WGS84
        Code(3857)  # Web Mercator
        utm_code = Code.create_utm(18, northern=True)  # UTM Zone 18N
        assert Code.is_utm_zone(utm_code)

        # Invalid EPSG codes (should raise ValueError)
        with pytest.raises(ValueError):
            Code(0)

        with pytest.raises(ValueError):
            Code(-1)

    def test_epsg_code_from_string(self):
        """Test creating EPSG code from string."""
        # Valid formats
        code2 = Code.from_string("EPSG:4326")

        assert code2.value == 4326

    def test_epsg_code_from_string_invalid(self):
        """Test creating EPSG code from invalid string."""
        with pytest.raises(ValueError):
            Code.from_string("invalid")

        with pytest.raises(ValueError):
            Code.from_string("EPSG:")

        with pytest.raises(ValueError):
            Code.from_string("EPSG:abc")

    def test_manager_epsg_lookup(self):
        """Test EPSG code lookup in Manager."""
        manager = Manager.global_instance()

        # Test lookup by integer
        code1 = Code(4326)
        assert isinstance(code1, Code)
        assert code1.value == 4326

        # Test lookup by string
        code2 = Manager.to_epsg_code("EPSG:4326")
        assert isinstance(code2, int)
        assert code2 == 4326

    def test_manager_epsg_description(self):
        """Test EPSG code description lookup."""
        manager = Manager.global_instance()

        # Test known EPSG codes
        code = Code(4326)
        desc = code.get_coordinate_type()
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_epsg_code_comparison(self):
        """Test EPSG code comparison operations."""
        code1 = Code(4326)  # WGS84
        code2 = Code(3857)  # Web Mercator
        code3 = Code(4978)  # ECEF

        # Test actual comparisons based on numeric values
        assert code1 > code2  # 4326 > 3857
        assert code3 > code2  # 4978 > 3857
        assert code3 > code1  # 4978 > 4326

    def test_epsg_code_sorting(self):
        """Test sorting EPSG codes."""
        codes = [Code(4978), Code(4326), Code(3857)]
        sorted_codes = sorted(codes)

        # Correct order: 3857, 4326, 4978
        expected = [Code(3857), Code(4326), Code(4978)]
        assert sorted_codes == expected
