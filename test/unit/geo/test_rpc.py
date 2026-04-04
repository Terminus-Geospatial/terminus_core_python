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
#    File:    test_rpc.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Unit tests for RPC (Rational Polynomial Coefficients) projector
"""

import pytest
import numpy as np

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import RPC, Transformation_Type


class TestRPC:
    """Test RPC projector implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = RPC()

        # Sample RPC coefficients (simplified for testing)
        self.rpc_coeffs = {
            'line_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # y = y
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'samp_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # x = x
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_line_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_offset': 0.0,
            'samp_offset': 0.0,
            'lat_offset': 0.0,
            'lon_offset': 0.0,
            'line_scale': 1.0,
            'samp_scale': 1.0,
            'lat_scale': 1.0,
            'lon_scale': 1.0,
        }

    def test_transformation_type(self):
        """Test transformation type property."""
        assert self.projector.transformation_type == Transformation_Type.RPC

    def test_is_identity(self):
        """Test is_identity property."""
        assert self.projector.is_identity is False

    def test_update_model(self):
        """Test updating RPC model with coefficients."""
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Verify coefficients are set
        assert self.projector._coeffs is not None
        assert self.projector._offsets is not None
        assert self.projector._scales is not None

    def test_update_model_missing_coeffs(self):
        """Test error when RPC coefficients are missing."""
        with pytest.raises(ValueError, match="rpc_coeffs required"):
            self.projector.update_model()

    def test_source_to_geographic_no_model(self):
        """Test error when transforming without model."""
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            self.projector.source_to_geographic(Pixel(100, 200))

    def test_geographic_to_source_no_model(self):
        """Test error when inverse transforming without model."""
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            self.projector.geographic_to_source(Geographic(35.0, -118.0))

    def test_identity_rpc_transformation(self):
        """Test RPC transformation with identity-like coefficients."""
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Test pixel to geographic
        pixel = Pixel(100.0, 35.0)  # Use latitude in valid range
        geo = self.projector.source_to_geographic(pixel)

        # With identity coefficients, should be approximately the same
        assert abs(geo.latitude_deg - pixel.y_px) < 1e-6
        assert abs(geo.longitude_deg - pixel.x_px) < 1e-6

    def test_inverse_rpc_transformation(self):
        """Test RPC inverse transformation."""
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Test geographic to pixel
        geo = Geographic(35.0, 100.0)  # Use valid latitude
        pixel = self.projector.geographic_to_source(geo)

        # With identity coefficients, should be approximately the same
        assert abs(pixel.x_px - geo.longitude_deg) < 1e-6
        assert abs(pixel.y_px - geo.latitude_deg) < 1e-6

    def test_roundtrip_transformation(self):
        """Test RPC roundtrip transformation."""
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        original_pixel = Pixel(150.5, 45.0)  # Use valid latitude
        geo = self.projector.source_to_geographic(original_pixel)
        result_pixel = self.projector.geographic_to_source(geo)

        # Should be very close to original
        assert abs(result_pixel.x_px - original_pixel.x_px) < 1e-6
        assert abs(result_pixel.y_px - original_pixel.y_px) < 1e-6

    def test_complex_rpc_coefficients(self):
        """Test RPC with more complex coefficients."""
        complex_coeffs = {
            'line_num_coefs': [0.1, 0.9, 0.05, 0.02, 0.01, 0.01, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, -0.1, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.05, 0.02, 0.95, -0.01, 0.01, 0.0, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.1, -0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_offset': 512.0,
            'samp_offset': 512.0,
            'lat_offset': 35.0,
            'lon_offset': -118.0,
            'line_scale': 512.0,
            'samp_scale': 512.0,
            'lat_scale': 10.0,
            'lon_scale': 10.0,
        }

        self.projector.update_model(rpc_coeffs=complex_coeffs)

        # Test transformation with complex coefficients
        pixel = Pixel(256.0, 256.0)  # Center of image
        geo = self.projector.source_to_geographic(pixel)

        # Should get reasonable geographic coordinates
        assert -180 <= geo.longitude_deg <= 180
        assert -90 <= geo.latitude_deg <= 90

    def test_polynomial_computation(self):
        """Test internal polynomial computation."""
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Test polynomial computation
        result = self.projector._compute_polynomial(0.5, 0.5, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])

        # Manual calculation for verification
        x, y = 0.5, 0.5
        expected = (1.0 + 2.0*x + 3.0*y + 4.0*x*y + 5.0*x*x + 6.0*y*y +
                   7.0*x*x*y + 8.0*x*y*y + 9.0*x*x*y*y)

        assert abs(result - expected) < 1e-10

    def test_rpc_identity_equivalent(self):
        """Test RPC with identity-equivalent coefficients."""
        # Identity RPC: normalized coordinates map directly to geographic
        identity_coeffs = {
            'line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # y = y
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # x = x
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # y = y
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # x = x
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'line_offset': 512.0,
            'samp_offset': 512.0,
            'lat_offset': 35.0,
            'lon_offset': -118.0,
            'line_scale': 512.0,
            'samp_scale': 512.0,
            'lat_scale': 10.0,
            'lon_scale': 10.0,
        }

        self.projector.update_model(rpc_coeffs=identity_coeffs)

        # Test multiple points for identity verification
        test_cases = [
            (Pixel(512.0, 512.0), Geographic(35.0, -118.0)),  # Center
            (Pixel(1024.0, 512.0), Geographic(35.0, -108.0)),  # East
            (Pixel(0.0, 512.0), Geographic(35.0, -128.0)),     # West
            (Pixel(512.0, 1024.0), Geographic(45.0, -118.0)),  # North
            (Pixel(512.0, 0.0), Geographic(25.0, -118.0)),     # South
        ]

        for pixel, expected_geo in test_cases:
            # Forward transformation
            geo = self.projector.source_to_geographic(pixel)
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

            # Inverse transformation
            result_pixel = self.projector.geographic_to_source(expected_geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 1e-6
            assert abs(result_pixel.y_px - pixel.y_px) < 1e-6

            # Roundtrip verification
            roundtrip_geo = self.projector.source_to_geographic(result_pixel)
            assert abs(roundtrip_geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
            assert abs(roundtrip_geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

    def test_rpc_complex_realistic_case(self):
        """Test RPC with realistic satellite imagery coefficients."""
        # Realistic RPC coefficients for a satellite image
        realistic_coeffs = {
            'line_num_coefs': [2.345, -0.0123, 0.0089, 0.0012, -0.0003, 0.0004, 0.0001, -0.0002, 0.0000],
            'line_den_coefs': [1.0, 0.0056, -0.0034, 0.0001, 0.0002, -0.0001, 0.0000, 0.0001, -0.0000],
            'samp_num_coefs': [1.234, 0.0078, -0.0067, -0.0008, 0.0005, -0.0003, -0.0001, 0.0002, 0.0000],
            'samp_den_coefs': [1.0, -0.0045, 0.0032, -0.0002, -0.0001, 0.0003, 0.0000, -0.0001, 0.0000],
            'inv_line_num_coefs': [0.8, 0.01, -0.008, 0.001, -0.0005, 0.0003, 0.0001, -0.0001, 0.0000],
            'inv_line_den_coefs': [1.0, -0.003, 0.002, 0.000, 0.0001, -0.0001, 0.0000, 0.0000, 0.0000],
            'inv_samp_num_coefs': [0.9, -0.009, 0.007, -0.001, 0.0004, -0.0002, -0.0001, 0.0001, 0.0000],
            'inv_samp_den_coefs': [1.0, 0.002, -0.001, 0.000, -0.0001, 0.0001, 0.0000, 0.0000, 0.0000],
            'line_offset': 2048.0,
            'samp_offset': 2048.0,
            'lat_offset': 40.0,
            'lon_offset': -105.0,
            'line_scale': 2048.0,
            'samp_scale': 2048.0,
            'lat_scale': 5.0,
            'lon_scale': 5.0,
        }

        self.projector.update_model(rpc_coeffs=realistic_coeffs)

        # Test points across the image
        test_pixels = [
            Pixel(1024.0, 1024.0),  # Quarter
            Pixel(3072.0, 1024.0),  # Three-quarters
            Pixel(2048.0, 2048.0),  # Center
            Pixel(512.0, 512.0),    # Upper-left
            Pixel(3584.0, 3584.0),  # Lower-right
        ]

        for pixel in test_pixels:
            # Forward transformation should produce valid geographic coordinates
            geo = self.projector.source_to_geographic(pixel)

            # Verify coordinates are in valid ranges
            assert -90 <= geo.latitude_deg <= 90, f"Invalid latitude: {geo.latitude_deg}"
            assert -180 <= geo.longitude_deg <= 180, f"Invalid longitude: {geo.longitude_deg}"

            # Inverse transformation should be reasonably close
            result_pixel = self.projector.geographic_to_source(geo)

            # Allow some tolerance due to simplified inverse
            assert abs(result_pixel.x_px - pixel.x_px) < 50.0
            assert abs(result_pixel.y_px - pixel.y_px) < 50.0

    def test_rpc_solver_verification(self):
        """Test RPC solver accuracy with known solutions."""
        # Create RPC coefficients with known analytical solution
        solver_coeffs = {
            'line_num_coefs': [0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # y = 2y
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'samp_num_coefs': [0.0, 3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # x = 3x
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # y = 0.5y
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_samp_num_coefs': [0.0, 0.333333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # x = x/3
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'line_offset': 0.0,
            'samp_offset': 0.0,
            'lat_offset': 0.0,
            'lon_offset': 0.0,
            'line_scale': 1.0,
            'samp_scale': 1.0,
            'lat_scale': 1.0,
            'lon_scale': 1.0,
        }

        self.projector.update_model(rpc_coeffs=solver_coeffs)

        # Test with known scaling factors
        test_pixel = Pixel(10.0, 20.0)

        # Forward: y' = 2*20 = 40, x' = 3*10 = 30
        geo = self.projector.source_to_geographic(test_pixel)
        expected_geo = Geographic(latitude_deg=40.0, longitude_deg=30.0)

        assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
        assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

        # Inverse: y = 40/2 = 20, x = 30/3 = 10
        result_pixel = self.projector.geographic_to_source(expected_geo)

        assert abs(result_pixel.x_px - test_pixel.x_px) < 1e-6
        assert abs(result_pixel.y_px - test_pixel.y_px) < 1e-6

        # Verify solver consistency
        for i in range(5):
            test_x = float(i * 10)
            test_y = float(i * 15)
            pixel = Pixel(test_x, test_y)

            # Forward transformation
            geo = self.projector.source_to_geographic(pixel)

            # Should be scaled by known factors
            assert abs(geo.latitude_deg - 2.0 * test_y) < 1e-6
            assert abs(geo.longitude_deg - 3.0 * test_x) < 1e-6

            # Inverse transformation
            result_pixel = self.projector.geographic_to_source(geo)

            # Should recover original coordinates
            assert abs(result_pixel.x_px - test_x) < 1e-6
            assert abs(result_pixel.y_px - test_y) < 1e-6
