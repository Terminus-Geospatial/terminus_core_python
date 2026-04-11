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
#    File:    test_flat.py
#    Author:  Marvin Smith
#    Date:    04/10/2026
#
"""
Unit tests for flat elevation source
"""

# Project Libraries
from tmns.geo.coord import Geographic
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.source.flat import Flat


class TestFlat:
    """Test flat elevation source."""

    def test_flat_creation(self):
        """Test creating flat elevation source."""
        flat = Flat(100.0)
        assert flat.elevation == 100.0
        assert flat.name == "Flat Surface"

    def test_flat_with_custom_name(self):
        """Test creating flat source with custom name."""
        flat = Flat(100.0, name="Custom Flat")
        assert flat.name == "Custom Flat"

    def test_contains_always_true(self):
        """Test that flat source contains all coordinates."""
        flat = Flat(100.0)
        coord = Geographic.create(40.7, -74.0)
        assert flat.contains(coord) is True

    def test_elevation_meters(self):
        """Test getting elevation from flat source."""
        flat = Flat(100.0)
        coord = Geographic.create(40.7, -74.0)
        elevation = flat.elevation_meters(coord)
        assert elevation == 100.0

    def test_elevation_meters_with_altitude(self):
        """Test elevation with coordinate that has altitude."""
        flat = Flat(100.0)
        coord = Geographic.create(40.7, -74.0, 50.0)
        elevation = flat.elevation_meters(coord)
        assert elevation == 100.0

    def test_set_elevation(self):
        """Test updating elevation value."""
        flat = Flat(100.0)
        assert flat.elevation == 100.0
        flat.set_elevation(200.0)
        assert flat.elevation == 200.0

    def test_info(self):
        """Test getting source information."""
        flat = Flat(100.0)
        info = flat.info()
        assert info['elevation'] == 100.0
        assert info['coverage'] == 'global'
        assert 'description' in info

    def test_negative_elevation(self):
        """Test flat source with negative elevation."""
        flat = Flat(-50.0)
        coord = Geographic.create(40.7, -74.0)
        elevation = flat.elevation_meters(coord)
        assert elevation == -50.0

    def test_zero_elevation(self):
        """Test flat source with zero elevation."""
        flat = Flat(0.0)
        coord = Geographic.create(40.7, -74.0)
        elevation = flat.elevation_meters(coord)
        assert elevation == 0.0
