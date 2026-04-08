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

from tmns.geo.coord import UTM, Geographic, Pixel
from tmns.geo.proj import GCP


class TestGCP:
    """Test GCP data structure."""

    def test_gcp_creation(self):
        """Test creating a basic GCP."""
        test_pixel = Pixel(100.0, 200.0)
        ref_pixel = Pixel(105.0, 205.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=1,
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geo
        )

        assert gcp.id == 1
        assert gcp.test_pixel == test_pixel
        assert gcp.reference_pixel == ref_pixel
        assert gcp.geographic == geo
        assert gcp.projected is None
        assert gcp.error is None
        assert gcp.enabled is True

    def test_gcp_with_utm_projection(self):
        """Test creating GCP with UTM projection."""
        test_pixel = Pixel(100.0, 200.0)
        ref_pixel = Pixel(105.0, 205.0)
        geo = Geographic(35.0, -118.0)
        utm = UTM.create(500000.0, 4000000.0, "EPSG:32611", 1000.0)

        gcp = GCP(
            id=2,
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geo,
            projected=utm,
            error=1.5,
            enabled=False
        )

        assert gcp.projected == utm
        assert gcp.error == 1.5
        assert gcp.enabled is False

    def test_gcp_validation_invalid_id(self):
        """Test GCP validation for invalid ID."""
        test_pixel = Pixel(100.0, 200.0)
        ref_pixel = Pixel(105.0, 205.0)
        geo = Geographic(35.0, -118.0)

        with pytest.raises(ValueError, match="GCP ID must be positive"):
            GCP(
                id=0,
                test_pixel=test_pixel,
                reference_pixel=ref_pixel,
                geographic=geo
            )

        with pytest.raises(ValueError, match="GCP ID must be positive"):
            GCP(
                id=-1,
                test_pixel=test_pixel,
                reference_pixel=ref_pixel,
                geographic=geo
            )

    def test_to_dict(self):
        """Test converting GCP to dictionary."""
        test_pixel = Pixel(100.0, 200.0)
        ref_pixel = Pixel(105.0, 205.0)
        geo = Geographic(35.0, -118.0, 1000.0)
        utm = UTM.create(500000.0, 4000000.0, "EPSG:32611", 1000.0)

        gcp = GCP(
            id=3,
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geo,
            projected=utm,
            error=2.5,
            enabled=True
        )

        result = gcp.to_dict()

        expected = {
            'id': 3,
            'test_pixel': {'x': 100.0, 'y': 200.0},
            'reference_pixel': {'x': 105.0, 'y': 205.0},
            'geographic': {'latitude': 35.0, 'longitude': -118.0, 'elevation': 1000.0},
            'projected': {
                'easting': 500000.0,
                'northing': 4000000.0,
                'elevation': 1000.0,
                'crs': 'EPSG:32611'
            },
            'error': 2.5,
            'enabled': True
        }

        assert result == expected

    def test_to_dict_no_projection(self):
        """Test converting GCP to dictionary without projection."""
        test_pixel = Pixel(100.0, 200.0)
        ref_pixel = Pixel(105.0, 205.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=4,
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geo
        )

        result = gcp.to_dict()

        assert result['projected'] is None
        assert result['error'] is None
        assert result['enabled'] is True

    def test_from_dict(self):
        """Test creating GCP from dictionary."""
        data = {
            'id': 5,
            'test_pixel': {'x': 150.0, 'y': 250.0},
            'reference_pixel': {'x': 155.0, 'y': 255.0},
            'geographic': {'latitude': 40.0, 'longitude': -115.0, 'elevation': 1500.0},
            'projected': {
                'easting': 600000.0,
                'northing': 4500000.0,
                'elevation': 1500.0,
                'crs': 'EPSG:32612'
            },
            'error': 3.5,
            'enabled': False
        }

        gcp = GCP.from_dict(data)

        assert gcp.id == 5
        assert gcp.test_pixel.x_px == 150.0
        assert gcp.test_pixel.y_px == 250.0
        assert gcp.reference_pixel.x_px == 155.0
        assert gcp.reference_pixel.y_px == 255.0
        assert gcp.geographic.latitude_deg == 40.0
        assert gcp.geographic.longitude_deg == -115.0
        assert gcp.geographic.altitude_m == 1500.0
        assert gcp.projected.easting_m == 600000.0
        assert gcp.projected.northing_m == 4500000.0
        assert gcp.projected.altitude_m == 1500.0
        assert gcp.projected.crs == 'EPSG:32612'
        assert gcp.error == 3.5
        assert gcp.enabled is False

    def test_from_dict_minimal(self):
        """Test creating GCP from minimal dictionary."""
        data = {
            'id': 6,
            'test_pixel': {'x': 200.0, 'y': 300.0},
            'reference_pixel': {'x': 205.0, 'y': 305.0},
            'geographic': {'latitude': 45.0, 'longitude': -112.0}
        }

        gcp = GCP.from_dict(data)

        assert gcp.id == 6
        assert gcp.test_pixel.x_px == 200.0
        assert gcp.test_pixel.y_px == 300.0
        assert gcp.geographic.latitude_deg == 45.0
        assert gcp.geographic.longitude_deg == -112.0
        assert gcp.geographic.altitude_m is None
        assert gcp.projected is None
        assert gcp.error is None
        assert gcp.enabled is True  # Default value

    def test_from_dict_default_crs(self):
        """Test creating GCP from dictionary with default CRS."""
        data = {
            'id': 7,
            'test_pixel': {'x': 250.0, 'y': 350.0},
            'reference_pixel': {'x': 255.0, 'y': 355.0},
            'geographic': {'latitude': 50.0, 'longitude': -110.0},
            'projected': {
                'easting': 700000.0,
                'northing': 5000000.0,
                'elevation': 2000.0
                # No CRS specified - should default to EPSG:3857
            }
        }

        gcp = GCP.from_dict(data)

        assert gcp.projected.crs == 'EPSG:3857'

    def test_str_representation(self):
        """Test string representation of GCP."""
        test_pixel = Pixel(100.0, 200.0)
        ref_pixel = Pixel(105.0, 205.0)
        geo = Geographic(35.0, -118.0)

        gcp = GCP(
            id=8,
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geo
        )

        str_repr = str(gcp)
        expected = "GCP 8: TestPixel(x=100.0, y=200.0) → GeoGeographic(35.000000, -118.000000)"
        assert str_repr == expected

    def test_roundtrip_dict_conversion(self):
        """Test roundtrip conversion through dictionary."""
        test_pixel = Pixel(300.0, 400.0)
        ref_pixel = Pixel(305.0, 405.0)
        geo = Geographic(55.0, -108.0, 2500.0)
        utm = UTM.create(800000.0, 5500000.0, "EPSG:32613", 2500.0)

        original_gcp = GCP(
            id=9,
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geo,
            projected=utm,
            error=4.5,
            enabled=False
        )

        # Convert to dict and back
        gcp_dict = original_gcp.to_dict()
        restored_gcp = GCP.from_dict(gcp_dict)

        assert restored_gcp.id == original_gcp.id
        assert restored_gcp.test_pixel.x_px == original_gcp.test_pixel.x_px
        assert restored_gcp.test_pixel.y_px == original_gcp.test_pixel.y_px
        assert restored_gcp.reference_pixel.x_px == original_gcp.reference_pixel.x_px
        assert restored_gcp.reference_pixel.y_px == original_gcp.reference_pixel.y_px
        assert restored_gcp.geographic.latitude_deg == original_gcp.geographic.latitude_deg
        assert restored_gcp.geographic.longitude_deg == original_gcp.geographic.longitude_deg
        assert restored_gcp.geographic.altitude_m == original_gcp.geographic.altitude_m
        assert restored_gcp.projected.easting_m == original_gcp.projected.easting_m
        assert restored_gcp.projected.northing_m == original_gcp.projected.northing_m
        assert restored_gcp.projected.altitude_m == original_gcp.projected.altitude_m
        assert restored_gcp.projected.crs == original_gcp.projected.crs
        assert restored_gcp.error == original_gcp.error
        assert restored_gcp.enabled == original_gcp.enabled
