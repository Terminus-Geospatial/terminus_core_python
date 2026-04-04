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
#    File:    test_projector_integration.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Integration tests for Projector API
"""

import pytest
import numpy as np

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import Transformation_Type, Identity, Affine


class TestProjector_Integration:
    """Integration tests for projector functionality."""

    def test_identity_roundtrip_precision(self):
        """Test identity projector roundtrip precision."""
        projector = Identity()

        # Test coordinates
        test_coords = [
            Geographic(latitude_deg=35.0, longitude_deg=-118.0),
            Geographic(latitude_deg=0.0, longitude_deg=0.0),
            Geographic(latitude_deg=90.0, longitude_deg=0.0),
            Geographic(latitude_deg=-90.0, longitude_deg=180.0),
            Geographic(latitude_deg=45.0, longitude_deg=-180.0),
        ]

        tolerance = 1e-10
        for geo in test_coords:
            # Geographic to pixel
            pixel = projector.geographic_to_source(geo)
            assert isinstance(pixel, Pixel)

            # Pixel back to geographic
            geo_result = projector.source_to_geographic(pixel)
            assert isinstance(geo_result, Geographic)

            # Check roundtrip precision
            lat_error = abs(geo_result.latitude_deg - geo.latitude_deg)
            lon_error = abs(geo_result.longitude_deg - geo.longitude_deg)

            assert lat_error < tolerance, f"Latitude precision loss: {lat_error}"
            assert lon_error < tolerance, f"Longitude precision loss: {lon_error}"

    def test_affine_basic_transformation(self):
        """Test affine projector basic transformation."""
        projector = Affine()

        # Set up a simple translation matrix
        transform_matrix = [
            [1.0, 0.0, 0.01],   # x' = x + 0.01
            [0.0, 1.0, -0.01],  # y' = y - 0.01
            [0.0, 0.0, 1.0]
        ]
        projector.update_model(transform_matrix=transform_matrix)

        # Test transformation
        test_pixel = Pixel(x_px=35.0, y_px=-118.0)
        geo = projector.source_to_geographic(test_pixel)

        # Should be translated by the matrix
        expected_geo = Geographic(latitude_deg=-118.01, longitude_deg=35.01)

        assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
        assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

    def test_affine_roundtrip_validation(self):
        """Test affine projector roundtrip validation."""
        projector = Affine()

        # Set up a simple scaling matrix
        transform_matrix = [
            [1.1, 0.0, 0.0],    # x' = 1.1*x
            [0.0, 0.9, 0.0],    # y' = 0.9*y
            [0.0, 0.0, 1.0]
        ]
        projector.update_model(transform_matrix=transform_matrix)

        # Test roundtrip: pixel -> geo -> pixel
        test_pixel = Pixel(x_px=10.0, y_px=20.0)
        geo = projector.source_to_geographic(test_pixel)
        result_pixel = projector.geographic_to_source(geo)

        # Should be close to original (allowing for transformation)
        tolerance = 1e-6
        assert abs(result_pixel.x_px - test_pixel.x_px) < tolerance
        assert abs(result_pixel.y_px - test_pixel.y_px) < tolerance

    def test_transformation_type_properties(self):
        """Test transformation type properties."""
        identity = Identity()
        affine = Affine()

        assert identity.transformation_type == Transformation_Type.IDENTITY
        assert affine.transformation_type == Transformation_Type.AFFINE

        assert identity.is_identity is True
        assert affine.is_identity is False

    def test_projector_image_attributes(self):
        """Test projector image attribute management."""
        projector = Identity()

        # Test source attributes
        projector.set_source_image_attributes(width=1000, height=800, crs="EPSG:4326")
        attrs = projector.source_image_attributes
        assert attrs["width"] == 1000
        assert attrs["height"] == 800
        assert attrs["crs"] == "EPSG:4326"

        # Test destination attributes
        projector.set_destination_image_attributes(width=500, height=400)
        attrs = projector.destination_image_attributes
        assert attrs["width"] == 500
        assert attrs["height"] == 400


class Test_RPC_TPS_Placeholder:
    """Placeholder tests for future RPC and TPS implementations."""

    @pytest.mark.skip(reason="RPC projector not yet implemented")
    def test_rpc_coefficient_loading(self):
        """Test loading RPC coefficients from GeoTIFF."""
        # TODO: Implement RPC projector and test coefficient parsing
        pass

    @pytest.mark.skip(reason="RPC projector not yet implemented")
    def test_rpc_transformation_accuracy(self):
        """Test RPC transformation accuracy."""
        # TODO: Implement RPC projector and test forward/inverse transformations
        pass

    @pytest.mark.skip(reason="TPS projector not yet implemented")
    def test_tps_interpolation_accuracy(self):
        """Test TPS interpolation accuracy."""
        # TODO: Implement TPS projector and test interpolation with control points
        pass
