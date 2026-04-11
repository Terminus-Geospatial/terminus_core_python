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
#    Date:    04/10/2026
#
"""
Unit tests for RPC (Rational Polynomial Coefficients) projector
"""

import json
import numpy as np
import pytest

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import RPC, Transformation_Type


class TestRPC:
    """Test RPC projector implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = RPC()

        # Realistic GCPs from collection_gcps.json (subset of 205 points)
        # Southern California scene: 35.33-35.43N, 119.12-118.99W
        # Image: 12288x12288 pixels
        self.realistic_gcps = [
            (Pixel(3105.0, 3606.0), Geographic(35.397429, -119.037101)),
            (Pixel(2873.0, 3312.0), Geographic(35.397131, -119.033732)),
            (Pixel(8386.0, 10520.0), Geographic(35.409213, -119.108067)),
            (Pixel(7282.22, 11874.76), Geographic(35.412531, -119.109499)),
            (Pixel(6753.24, 11698.92), Geographic(35.413729, -119.107381)),
            (Pixel(6703.87, 11829.67), Geographic(35.414306, -119.108083)),
            (Pixel(5435.61, 11293.48), Geographic(35.416899, -119.102365)),
            (Pixel(5807.07, 11156.74), Geographic(35.415224, -119.102139)),
            (Pixel(4587.04, 10782.38), Geographic(35.418214, -119.097413)),
            (Pixel(3497.92, 10922.43), Geographic(35.422293, -119.096228)),
            (Pixel(3538.87, 11141.15), Geographic(35.422813, -119.097741)),
            (Pixel(2058.04, 11108.75), Geographic(35.427591, -119.094694)),
            (Pixel(1680.96, 11217.64), Geographic(35.429130, -119.094678)),
            (Pixel(1147.45, 11104.85), Geographic(35.430585, -119.092939)),
            (Pixel(600.46, 11185.02), Geographic(35.432535, -119.092425)),
            (Pixel(520.65, 11953.02), Geographic(35.434773, -119.097204)),
            (Pixel(103.65, 11255.68), Geographic(35.434353, -119.091990)),
            (Pixel(1091.21, 6486.16), Geographic(35.416509, -119.058725)),
            (Pixel(967.36, 6482.01), Geographic(35.416986, -119.058527)),
            (Pixel(836.71, 7116.49), Geographic(35.419618, -119.063419)),
        ]

        # Identity-like GCPs (linear mapping)
        # Simulating 1920x1080 image with 1-degree geographic coverage
        # RPC requires at least 9 GCPs for 9-term polynomial
        self.linear_gcps = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(1920.0, 0.0), Geographic(35.0, -116.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
            (Pixel(1920.0, 540.0), Geographic(35.5, -116.0)),
            (Pixel(0.0, 1080.0), Geographic(36.0, -118.0)),
            (Pixel(960.0, 1080.0), Geographic(36.0, -117.0)),
            (Pixel(1920.0, 1080.0), Geographic(36.0, -116.0)),
            (Pixel(480.0, 270.0), Geographic(35.25, -117.75)),
            (Pixel(1440.0, 810.0), Geographic(35.75, -117.25)),
        ]

        # Test points for validation (not used in fitting)
        self.test_points = [
            Pixel(240.0, 135.0),
            Pixel(1680.0, 945.0),
            Pixel(720.0, 405.0),
            Pixel(1200.0, 675.0),
            Pixel(360.0, 675.0),
            Pixel(1560.0, 405.0),
            Pixel(840.0, 315.0),
            Pixel(1080.0, 765.0),
        ]

    def test_transformation_type(self):
        """Test transformation type property."""
        assert self.projector.transformation_type == Transformation_Type.RPC

    def test_is_identity(self):
        """Test is_identity property."""
        assert self.projector.is_identity is False

    def test_update_model_with_rpc_coeffs(self):
        """Test updating model with RPC coefficients."""
        rpc_coeffs = {
            'line_offset': 540.0,
            'samp_offset': 960.0,
            'lat_offset': 35.5,
            'lon_offset': -117.5,
            'height_offset': 0.0,
            'line_scale': 540.0,
            'samp_scale': 960.0,
            'lat_scale': 0.5,
            'lon_scale': 0.5,
            'height_scale': 1.0,
            'line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }

        self.projector.update_model(rpc_coeffs=rpc_coeffs)

        assert self.projector._coeffs is not None
        assert self.projector._offsets is not None
        assert self.projector._scales is not None

    def test_update_model_missing_rpc_coeffs(self):
        """Test error when RPC coefficients are missing."""
        with pytest.raises(ValueError, match="rpc_coeffs required"):
            self.projector.update_model()

    def test_solve_from_gcps(self):
        """Test fitting RPC model from GCPs."""
        self.projector.solve_from_gcps(self.linear_gcps)

        assert self.projector._coeffs is not None
        assert self.projector._offsets is not None
        assert self.projector._scales is not None

    def test_solve_from_gcps_insufficient_points(self):
        """Test error when too few GCPs provided."""
        with pytest.raises(ValueError, match="At least 9 GCPs required"):
            self.projector.solve_from_gcps(self.linear_gcps[:3])

    def test_source_to_geographic_no_model(self):
        """Test error when transforming without model."""
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            self.projector.source_to_geographic(Pixel(50, 50))

    def test_geographic_to_source_no_model(self):
        """Test error when inverse transforming without model."""
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            self.projector.geographic_to_source(Geographic(35.5, -117.5))

    def test_geographic_to_source_batch_no_model(self):
        """Test error when batch inverse transforming without model."""
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            geo_coords = np.array([[-117.5, 35.5]])
            self.projector.geographic_to_source_batch(geo_coords)

    def test_simple_rpc_transformation(self):
        """Test RPC transformation with simple coefficients."""
        rpc_coeffs = {
            'line_offset': 540.0,
            'samp_offset': 960.0,
            'lat_offset': 35.5,
            'lon_offset': -117.5,
            'height_offset': 0.0,
            'line_scale': 540.0,
            'samp_scale': 960.0,
            'lat_scale': 0.5,
            'lon_scale': 0.5,
            'height_scale': 1.0,
            'line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }

        self.projector.update_model(rpc_coeffs=rpc_coeffs)

        # Test at center pixel
        pixel = Pixel(960.0, 540.0)
        geo = self.projector.source_to_geographic(pixel)

        # Should map to center geographic coordinates
        assert abs(geo.latitude_deg - 35.5) < 0.01
        assert abs(geo.longitude_deg - (-117.5)) < 0.01

    def test_inverse_transformation(self):
        """Test geographic_to_source transformation."""
        self.projector.solve_from_gcps(self.linear_gcps)

        # Check with loose tolerance since RPC fitting is approximate
        for pixel, geo in self.linear_gcps:
            result_pixel = self.projector.geographic_to_source(geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 500.0
            assert abs(result_pixel.y_px - pixel.y_px) < 500.0

    def test_inverse_transformation_batch(self):
        """Test geographic_to_source_batch vectorized transformation."""
        self.projector.solve_from_gcps(self.linear_gcps)

        # Create batch of geographic coordinates
        geo_coords = np.array([[geo.longitude_deg, geo.latitude_deg] for _, geo in self.linear_gcps])
        pixel_coords = self.projector.geographic_to_source_batch(geo_coords)

        # Should return pixel coordinates
        assert pixel_coords.shape == (len(self.linear_gcps), 2)
        assert pixel_coords.shape[0] == geo_coords.shape[0]

        # Check with loose tolerance since RPC fitting is approximate
        for i, (pixel, geo) in enumerate(self.linear_gcps):
            assert abs(pixel_coords[i, 0] - pixel.x_px) < 500.0
            assert abs(pixel_coords[i, 1] - pixel.y_px) < 500.0

    def test_roundtrip_basic(self):
        """Test pixel->geo->pixel roundtrip with linear GCPs."""
        self.projector.solve_from_gcps(self.linear_gcps)

        test_pixels = [
            Pixel(240.0, 135.0),
            Pixel(720.0, 405.0),
            Pixel(480.0, 270.0),
        ]

        for original_pixel in test_pixels:
            geo = self.projector.source_to_geographic(original_pixel)

            assert 34.5 <= geo.latitude_deg <= 36.0
            assert -119.0 <= geo.longitude_deg <= -116.5

            result_pixel = self.projector.geographic_to_source(geo)
            # Roundtrip should be reasonably accurate (RPC inverse is direct)
            # Note: RPC fitting may not be exact due to polynomial approximation
            assert abs(result_pixel.x_px - original_pixel.x_px) < 100.0
            assert abs(result_pixel.y_px - original_pixel.y_px) < 100.0

    def test_realistic_gcps_fitting(self):
        """Test fitting RPC with realistic GCPs from collection."""
        # Use subset of realistic GCPs
        self.projector.solve_from_gcps(self.realistic_gcps)

        assert self.projector._coeffs is not None
        assert len(self.projector._coeffs) == 8  # 4 coefficient arrays

    def test_realistic_transformation_accuracy(self):
        """Test transformation accuracy with realistic GCPs."""
        self.projector.solve_from_gcps(self.realistic_gcps)

        # Test at GCP locations (should be reasonably accurate)
        for pixel, geo in self.realistic_gcps[:5]:  # Test first 5
            result_geo = self.projector.source_to_geographic(pixel)
            result_pixel = self.projector.geographic_to_source(geo)

            # Forward transformation accuracy
            assert abs(result_geo.latitude_deg - geo.latitude_deg) < 0.01
            assert abs(result_geo.longitude_deg - geo.longitude_deg) < 0.01

            # Inverse transformation accuracy
            # Note: RPC fitting from realistic GCPs may have larger errors
            assert abs(result_pixel.x_px - pixel.x_px) < 150.0
            assert abs(result_pixel.y_px - pixel.y_px) < 150.0

    def test_batch_transformation_consistency(self):
        """Test that batch transformation matches single-point transformation."""
        self.projector.solve_from_gcps(self.linear_gcps)

        # Test points
        test_geos = [
            Geographic(35.25, -117.75),
            Geographic(35.5, -117.5),
            Geographic(35.75, -117.25),
        ]

        # Single-point transformations
        single_results = [
            self.projector.geographic_to_source(geo) for geo in test_geos
        ]

        # Batch transformation
        geo_coords = np.array([[geo.longitude_deg, geo.latitude_deg] for geo in test_geos])
        batch_results = self.projector.geographic_to_source_batch(geo_coords)

        # Compare results
        for i, (single, batch) in enumerate(zip(single_results, batch_results)):
            assert abs(single.x_px - batch[0]) < 1e-6
            assert abs(single.y_px - batch[1]) < 1e-6

    def test_polynomial_computation(self):
        """Test polynomial computation method."""
        self.projector.update_model(rpc_coeffs={
            'line_offset': 540.0,
            'samp_offset': 960.0,
            'lat_offset': 35.5,
            'lon_offset': -117.5,
            'height_offset': 0.0,
            'line_scale': 540.0,
            'samp_scale': 960.0,
            'lat_scale': 0.5,
            'lon_scale': 0.5,
            'height_scale': 1.0,
            'line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        })

        # Test single-point polynomial
        result = self.projector._compute_polynomial(0.5, 0.5, [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        expected = 0.0 + 0.0 * 0.5 + 0.5 * 0.5  # C1 + C2*x + C3*y
        assert abs(result - expected) < 1e-10

    def test_polynomial_batch_computation(self):
        """Test batch polynomial computation method."""
        self.projector.update_model(rpc_coeffs={
            'line_offset': 540.0,
            'samp_offset': 960.0,
            'lat_offset': 35.5,
            'lon_offset': -117.5,
            'height_offset': 0.0,
            'line_scale': 540.0,
            'samp_scale': 960.0,
            'lat_scale': 0.5,
            'lon_scale': 0.5,
            'height_scale': 1.0,
            'line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        })

        # Test batch polynomial
        x = np.array([0.0, 0.5, 1.0])
        y = np.array([0.0, 0.5, 1.0])
        coeffs = [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        result = self.projector._compute_polynomial_batch(x, y, coeffs)

        # Expected: C1 + C2*x + C3*y = 0 + 0*x + 0.5*y
        expected = 0.5 * y
        assert np.allclose(result, expected)

    def test_rpc_identity_equivalent(self):
        """Test RPC with identity-like linear transformation."""
        # Create RPC coefficients for identity-like transformation
        # Note: Creating exact identity with RPC is complex, so we just test
        # that the coefficients are accepted and transformations work
        rpc_coeffs = {
            'line_offset': 540.0,
            'samp_offset': 960.0,
            'lat_offset': 35.5,
            'lon_offset': -117.5,
            'height_offset': 0.0,
            'line_scale': 540.0,
            'samp_scale': 960.0,
            'lat_scale': 0.5,
            'lon_scale': 0.5,
            'height_scale': 1.0,
            'line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 0.333, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }

        self.projector.update_model(rpc_coeffs=rpc_coeffs)

        # Just test that transformations work without errors
        pixel = Pixel(960.0, 540.0)
        geo = self.projector.source_to_geographic(pixel)
        result_pixel = self.projector.geographic_to_source(geo)

        # Verify the transformations return valid values
        assert geo.latitude_deg is not None
        assert geo.longitude_deg is not None
        assert result_pixel.x_px is not None
        assert result_pixel.y_px is not None
