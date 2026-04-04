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
#    File:    test_datum.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Unit tests for datum definitions.
"""

# Third-Party Libraries
import pytest

# Project Libraries
from tmns.geo.datum import Datum, Vertical_Datum


class Test_Datum:
    """Test Datum enum."""

    def test_datum_values(self):
        """Test datum enum values."""
        assert Datum.WGS84.value == "EPSG:4326"
        assert Datum.NAD83.value == "EPSG:4269"
        assert Datum.EGM96.value == "EPSG:5773"
        assert Datum.NAVD88.value == "EPSG:5703"

    def test_datum_names(self):
        """Test datum enum names."""
        assert Datum.WGS84.name == "WGS84"
        assert Datum.NAD83.name == "NAD83"
        assert Datum.EGM96.name == "EGM96"
        assert Datum.NAVD88.name == "NAVD88"

    def test_datum_iteration(self):
        """Test iterating over datum enum."""
        datums = list(Datum)
        assert len(datums) == 4
        assert Datum.WGS84 in datums
        assert Datum.NAD83 in datums
        assert Datum.EGM96 in datums
        assert Datum.NAVD88 in datums

    def test_datum_from_string(self):
        """Test creating datum from string value."""
        assert Datum("EPSG:4326") == Datum.WGS84
        assert Datum("EPSG:4269") == Datum.NAD83
        assert Datum("EPSG:5773") == Datum.EGM96
        assert Datum("EPSG:5703") == Datum.NAVD88

    def test_datum_from_name(self):
        """Test creating datum from name."""
        assert Datum["WGS84"] == Datum.WGS84
        assert Datum["NAD83"] == Datum.NAD83
        assert Datum["EGM96"] == Datum.EGM96
        assert Datum["NAVD88"] == Datum.NAVD88


class Test_Vertical_Datum:
    """Test Vertical_Datum enum."""

    def test_vertical_datum_values(self):
        """Test vertical datum enum values."""
        assert Vertical_Datum.EGM96.value == "EPSG:5773"
        assert Vertical_Datum.NAVD88.value == "EPSG:5703"
        assert Vertical_Datum.MSL.value == "EPSG:5714"

    def test_vertical_datum_names(self):
        """Test vertical datum enum names."""
        assert Vertical_Datum.EGM96.name == "EGM96"
        assert Vertical_Datum.NAVD88.name == "NAVD88"
        assert Vertical_Datum.MSL.name == "MSL"

    def test_vertical_datum_iteration(self):
        """Test iterating over vertical datum enum."""
        vertical_datums = list(Vertical_Datum)
        assert len(vertical_datums) == 3
        assert Vertical_Datum.EGM96 in vertical_datums
        assert Vertical_Datum.NAVD88 in vertical_datums
        assert Vertical_Datum.MSL in vertical_datums

    def test_vertical_datum_from_string(self):
        """Test creating vertical datum from string value."""
        assert Vertical_Datum("EPSG:5773") == Vertical_Datum.EGM96
        assert Vertical_Datum("EPSG:5703") == Vertical_Datum.NAVD88
        assert Vertical_Datum("EPSG:5714") == Vertical_Datum.MSL

    def test_vertical_datum_from_name(self):
        """Test creating vertical datum from name."""
        assert Vertical_Datum["EGM96"] == Vertical_Datum.EGM96
        assert Vertical_Datum["NAVD88"] == Vertical_Datum.NAVD88
        assert Vertical_Datum["MSL"] == Vertical_Datum.MSL


class Test_Datum_Relationships:
    """Test relationships between datums."""

    def test_shared_datums(self):
        """Test datums that appear in both enums."""
        # EGM96 and NAVD88 appear in both datum enums
        assert Datum.EGM96.value == Vertical_Datum.EGM96.value
        assert Datum.NAVD88.value == Vertical_Datum.NAVD88.value

    def test_datum_descriptions(self):
        """Test that datum values are valid EPSG codes."""
        # All values should be valid EPSG codes
        for datum in Datum:
            assert datum.value.startswith("EPSG:")
            assert datum.value[5:].isdigit()  # After "EPSG:" should be digits

        for vertical_datum in Vertical_Datum:
            assert vertical_datum.value.startswith("EPSG:")
            assert vertical_datum.value[5:].isdigit()  # After "EPSG:" should be digits
