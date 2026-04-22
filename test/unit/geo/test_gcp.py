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
#    File:    test_gcp.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Unit tests for GCP (Ground Control Point) class
"""

import pytest

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import GCP


class TestGCP:
    """Test GCP data structure."""

    def test_gcp_creation(self):
        """Test creating a basic GCP."""
        pixel = Pixel(100.0, 200.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=1,
            pixel=pixel,
            geographic=geo
        )

        assert gcp.id == 1
        assert gcp.pixel == pixel
        assert gcp.geographic == geo
        assert gcp.error is None
        assert gcp.enabled is True

    def test_gcp_with_error_and_disabled(self):
        """Test creating GCP with error and disabled flag."""
        pixel = Pixel(100.0, 200.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=2,
            pixel=pixel,
            geographic=geo,
            error=1.5,
            enabled=False
        )

        assert gcp.error == 1.5
        assert gcp.enabled is False

    def test_gcp_validation_invalid_id(self):
        """Test GCP validation for invalid ID."""
        pixel = Pixel(100.0, 200.0)
        geo = Geographic(35.0, -118.0)

        with pytest.raises(ValueError, match="GCP ID must be positive"):
            GCP(
                id=0,
                pixel=pixel,
                geographic=geo
            )

        with pytest.raises(ValueError, match="GCP ID must be positive"):
            GCP(
                id=-1,
                pixel=pixel,
                geographic=geo
            )

    def test_to_dict(self):
        """Test converting GCP to dictionary."""
        pixel = Pixel(100.0, 200.0)
        geo = Geographic(35.0, -118.0, 1000.0)

        gcp = GCP(
            id=3,
            pixel=pixel,
            geographic=geo,
            error=2.5,
            enabled=True
        )

        result = gcp.to_dict()

        expected = {
            'id': 3,
            'pixel': {'x': 100.0, 'y': 200.0},
            'geographic': {'latitude': 35.0, 'longitude': -118.0, 'elevation': 1000.0},
            'error': 2.5,
            'enabled': True
        }

        assert result == expected

    def test_to_dict_defaults(self):
        """Test converting GCP to dictionary with default values."""
        pixel = Pixel(100.0, 200.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=4,
            pixel=pixel,
            geographic=geo
        )

        result = gcp.to_dict()

        assert result['error'] is None
        assert result['enabled'] is True

    def test_from_dict(self):
        """Test creating GCP from dictionary."""
        data = {
            'id': 5,
            'pixel': {'x': 150.0, 'y': 250.0},
            'geographic': {'latitude': 40.0, 'longitude': -115.0, 'elevation': 1500.0},
            'error': 3.5,
            'enabled': False
        }

        gcp = GCP.from_dict(data)

        assert gcp.id == 5
        assert gcp.pixel.x_px == 150.0
        assert gcp.pixel.y_px == 250.0
        assert gcp.geographic.latitude_deg == 40.0
        assert gcp.geographic.longitude_deg == -115.0
        assert gcp.geographic.altitude_m == 1500.0
        assert gcp.error == 3.5
        assert gcp.enabled is False

    def test_from_dict_minimal(self):
        """Test creating GCP from minimal dictionary."""
        data = {
            'id': 6,
            'pixel': {'x': 200.0, 'y': 300.0},
            'geographic': {'latitude': 45.0, 'longitude': -112.0}
        }

        gcp = GCP.from_dict(data)

        assert gcp.id == 6
        assert gcp.pixel.x_px == 200.0
        assert gcp.pixel.y_px == 300.0
        assert gcp.geographic.latitude_deg == 45.0
        assert gcp.geographic.longitude_deg == -112.0
        assert gcp.geographic.altitude_m is None
        assert gcp.error is None
        assert gcp.enabled is True  # Default value

    def test_from_dict_with_altitude_none(self):
        """Test creating GCP from dictionary with no altitude."""
        data = {
            'id': 7,
            'pixel': {'x': 250.0, 'y': 350.0},
            'geographic': {'latitude': 50.0, 'longitude': -110.0}
        }

        gcp = GCP.from_dict(data)

        assert gcp.geographic.altitude_m is None

    def test_str_representation(self):
        """Test string representation of GCP."""
        pixel = Pixel(100.0, 200.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=8,
            pixel=pixel,
            geographic=geo
        )

        str_repr = str(gcp)
        expected = "GCP 8: TestPixel(x=100.0, y=200.0) → GeoGeographic(35.000000, -118.000000)"
        assert str_repr == expected

    def test_roundtrip_dict_conversion(self):
        """Test roundtrip conversion through dictionary."""
        pixel = Pixel(300.0, 400.0)
        geo = Geographic(55.0, -108.0, 2500.0)

        original_gcp = GCP(
            id=9,
            pixel=pixel,
            geographic=geo,
            error=4.5,
            enabled=False
        )

        # Convert to dict and back
        gcp_dict = original_gcp.to_dict()
        restored_gcp = GCP.from_dict(gcp_dict)

        assert restored_gcp.id == original_gcp.id
        assert restored_gcp.pixel.x_px == original_gcp.pixel.x_px
        assert restored_gcp.pixel.y_px == original_gcp.pixel.y_px
        assert restored_gcp.geographic.latitude_deg == original_gcp.geographic.latitude_deg
        assert restored_gcp.geographic.longitude_deg == original_gcp.geographic.longitude_deg
        assert restored_gcp.geographic.altitude_m == original_gcp.geographic.altitude_m
        assert restored_gcp.error == original_gcp.error
        assert restored_gcp.enabled == original_gcp.enabled
