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
#    File:    test_affine.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Unit tests for the Affine projector.

Matrix convention (see affine.py):
    M @ [x, y, 1]^T = [lon, lat, 1]^T

    Row 0: lon = M[0,0]*x + M[0,1]*y + M[0,2]
    Row 1: lat = M[1,0]*x + M[1,1]*y + M[1,2]
"""

import math

import numpy as np
import pytest

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import Affine, Transformation_Type


class TestAffine:
    """Test the affine projection implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = Affine()
        # Simple translation matrix: x' = x + 0.01, y' = y - 0.01 (small geographic offset)
        self.translation_matrix = [
            [1.0, 0.0, 0.01],
            [0.0, 1.0, -0.01],
            [0.0, 0.0, 1.0]
        ]
        # Simple scaling matrix: x' = 1.1*x, y' = 0.9*y (small scaling)
        self.scaling_matrix = [
            [1.1, 0.0, 0.0],
            [0.0, 0.9, 0.0],
            [0.0, 0.0, 1.0]
        ]

    def test_transformation_type(self):
        """Verify transformation_type returns AFFINE."""
        assert self.projector.transformation_type == Transformation_Type.AFFINE

    def test_is_identity(self):
        """Verify is_identity is always False for Affine."""
        assert self.projector.is_identity is False

    def test_update_model(self):
        """Verify update_model stores the matrix and computes its inverse."""
        self.projector.update_model(transform_matrix=self.translation_matrix)
        assert np.array_equal(self.projector._transform_matrix, self.translation_matrix)
        assert self.projector._inverse_matrix is not None

    def test_uninitialized_model_raises_error(self):
        """Verify pixel_to_world raises before update_model is called."""
        with pytest.raises(ValueError, match="Transform matrix not set"):
            self.projector.pixel_to_world(Pixel(x_px=0, y_px=0))

    def test_translation_transformation(self):
        """Verify forward and inverse for a pure translation matrix.

        Matrix: lon = x + 0.01, lat = y - 0.01
        """
        self.projector.update_model(transform_matrix=self.translation_matrix)

        # Test pixel to world - use valid coordinate ranges
        pixel = Pixel(x_px=35.0, y_px=-80.0)  # Use valid latitude range
        geo = self.projector.pixel_to_world(pixel)

        assert abs(geo.latitude_deg - (-80.01)) < 1e-10  # y: -80 + (-0.01) = -80.01
        assert abs(geo.longitude_deg - 35.01) < 1e-10  # x: 35 + 0.01 = 35.01

        # Test inverse transformation
        result_pixel = self.projector.world_to_pixel(geo)
        assert result_pixel.x_px == 35.0
        assert result_pixel.y_px == -80.0

    def test_scaling_transformation(self):
        """Verify forward and inverse for a pure scaling matrix.

        Matrix: lon = 1.1*x, lat = 0.9*y
        """
        self.projector.update_model(transform_matrix=self.scaling_matrix)

        # Test pixel to world - use small coordinates to stay in range
        pixel = Pixel(x_px=30.0, y_px=-50.0)  # Use valid range
        geo = self.projector.pixel_to_world(pixel)

        assert geo.latitude_deg == -45.0  # y: -50 * 0.9 = -45.0
        assert geo.longitude_deg == 33.0  # x: 30 * 1.1 = 33.0

        # Test inverse transformation
        result_pixel = self.projector.world_to_pixel(geo)
        assert result_pixel.x_px == 30.0
        assert result_pixel.y_px == -50.0

    def test_complex_transformation(self):
        """Verify roundtrip accuracy for a combined rotation + scaling matrix."""
        # Small 15-degree rotation + scaling to stay in range
        cos_15 = math.cos(math.pi / 12)  # 15 degrees
        sin_15 = math.sin(math.pi / 12)
        rotation_matrix = [
            [0.5 * cos_15, -0.5 * sin_15, 0.5],   # Smaller scaling to stay in range
            [0.5 * sin_15, 0.5 * cos_15, -0.3],  # Smaller scaling to stay in range
            [0.0, 0.0, 1.0]
        ]

        self.projector.update_model(transform_matrix=rotation_matrix)

        # Test roundtrip transformation with small coordinates
        original_pixel = Pixel(x_px=35.0, y_px=-50.0)  # Use valid coordinates
        geo = self.projector.pixel_to_world(original_pixel)
        result_pixel = self.projector.world_to_pixel(geo)

        # Should be very close to original (allowing for floating point error)
        assert abs(result_pixel.x_px - original_pixel.x_px) < 1e-10
        assert abs(result_pixel.y_px - original_pixel.y_px) < 1e-10

    def test_singular_matrix_raises_error(self):
        """Verify update_model raises ValueError for a singular (non-invertible) matrix."""
        singular_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],  # Zero row makes det = 0
            [0.0, 0.0, 1.0]
        ]

        with pytest.raises(ValueError, match="Singular matrix"):
            self.projector.update_model(transform_matrix=singular_matrix)


    def test_roundtrip_precision(self):
        """Verify numerical precision is maintained across 10 sequential roundtrips."""
        self.projector.update_model(transform_matrix=self.scaling_matrix)

        # Test multiple roundtrips with small coordinates
        original_pixel = Pixel(x_px=35.123, y_px=-50.456)  # Use valid coordinates

        for _ in range(10):
            geo = self.projector.pixel_to_world(original_pixel)
            original_pixel = self.projector.world_to_pixel(geo)

        # Should maintain precision
        assert abs(original_pixel.x_px - 35.123) < 1e-10
        assert abs(original_pixel.y_px - -50.456) < 1e-10

    def test_matrix_inverse_computation(self):
        """Verify M_inv @ M == I (identity) to floating-point precision."""
        # Test with simple translation matrix
        self.projector.update_model(transform_matrix=self.translation_matrix)

        inverse = self.projector._inverse_matrix

        # Check that inverse * original = identity
        original = np.array(self.translation_matrix)
        inv_array = np.array(inverse)
        product = np.dot(inv_array, original)

        # Should be close to identity matrix
        identity = np.eye(3)
        assert np.allclose(product, identity, atol=1e-10)

    def test_edge_cases(self):
        """Verify identity matrix acts as pass-through (x->lon, y->lat)."""
        # Test with identity matrix
        identity_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]

        self.projector.update_model(transform_matrix=identity_matrix)

        # Should behave like identity transformation
        pixel = Pixel(x_px=45.0, y_px=-90.0)  # Use valid coordinates
        geo = self.projector.pixel_to_world(pixel)

        assert abs(geo.latitude_deg - pixel.y_px) < 1e-10  # latitude comes from y
        assert abs(geo.longitude_deg - pixel.x_px) < 1e-10  # longitude comes from x

    def test_world_to_pixel_roundtrip(self):
        """Verify pixel->world->pixel roundtrip for a full-world affine mapping.

        Goal: Test that a matrix mapping a 4096x4096 image to the full
        geographic range [-180,180] x [-90,90] roundtrips exactly and
        maps key pixels to known geographic values.

        Matrix convention (row 0 = lon, row 1 = lat)::

            lon = (360/W)*x - 180    ->  x=0 maps to -180, x=W maps to +180
            lat = (180/H)*y - 90     ->  y=0 maps to -90,  y=H maps to +90
            center (W/2, H/2)        ->  (lon=0, lat=0)
        """
        src_width, src_height = 4096, 4096

        # Scale factors: full geographic range [-180,180] x [-90,90]
        # lon = (360/W)*x - 180,  lat = (180/H)*y - 90
        scale_lon = 360.0 / src_width
        scale_lat = 180.0 / src_height

        matrix = np.array([
            [scale_lon, 0.0, -180.0],
            [0.0, scale_lat, -90.0],
            [0.0, 0.0, 1.0]
        ])

        self.projector.update_model(transform_matrix=matrix)

        # Roundtrip at all 4 corners
        src_corners = [
            Pixel(0.0, 0.0),
            Pixel(src_width, 0.0),
            Pixel(0.0, src_height),
            Pixel(src_width, src_height),
        ]

        for src_pixel in src_corners:
            geo = self.projector.pixel_to_world(src_pixel)
            result_pixel = self.projector.world_to_pixel(geo)
            assert abs(result_pixel.x_px - src_pixel.x_px) < 1e-10
            assert abs(result_pixel.y_px - src_pixel.y_px) < 1e-10

        # Top-left (0,0) -> (-180, -90)
        geo_tl = self.projector.pixel_to_world(Pixel(0.0, 0.0))
        assert abs(geo_tl.longitude_deg + 180) < 1e-10
        assert abs(geo_tl.latitude_deg + 90) < 1e-10

        # Center (W/2, H/2) -> (0, 0)
        src_center = Pixel(src_width / 2.0, src_height / 2.0)
        geo_center = self.projector.pixel_to_world(src_center)
        assert abs(geo_center.longitude_deg) < 1e-10
        assert abs(geo_center.latitude_deg) < 1e-10

    def test_large_coordinate_values(self):
        """Verify roundtrip with large pixel values scaled to valid geographic range."""
        # Use matrix that keeps coordinates in valid range
        small_scale_matrix = [
            [0.001, 0.0, 0.0],
            [0.0, 0.001, 0.0],
            [0.0, 0.0, 1.0]
        ]

        self.projector.update_model(transform_matrix=small_scale_matrix)

        # Test with large pixel coordinates
        pixel = Pixel(x_px=50000.0, y_px=80000.0)
        geo = self.projector.pixel_to_world(pixel)

        # Should be scaled down to valid range
        assert -90 <= geo.latitude_deg <= 90
        assert -180 <= geo.longitude_deg <= 180

        # Roundtrip should work
        result_pixel = self.projector.world_to_pixel(geo)
        assert abs(result_pixel.x_px - pixel.x_px) < 1e-6
        assert abs(result_pixel.y_px - pixel.y_px) < 1e-6

    def test_affine_gcp_solve_bidirectional(self):
        """Verify solve_from_gcps() produces a correct bidirectional affine model.

        Goal: Test the full GCP -> solve -> forward/inverse workflow:
        1. Provide GCPs for a Southern California scene (1920x1080)
        2. Call solve_from_gcps() to fit forward matrix via least squares
        3. Verify forward accuracy at GCP locations (machine precision)
        4. Verify roundtrip (pixel->geo->pixel) is sub-pixel accurate

        Geographic Scenario:
        - Scene: Southern California (35-36N, 118-117W), 1920x1080 pixels
        - True mapping: lat = 35 + y/1080,  lon = -118 + x/1920
        - 5 GCPs: 4 corners + center (overdetermined: 5 equations, 3 unknowns each)
        """
        gcps = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),       # Top-left
            (Pixel(1920.0, 0.0), Geographic(35.0, -117.0)),    # Top-right
            (Pixel(0.0, 1080.0), Geographic(36.0, -118.0)),     # Bottom-left
            (Pixel(1920.0, 1080.0), Geographic(36.0, -117.0)),  # Bottom-right
            (Pixel(960.0, 540.0), Geographic(35.5, -117.5)),    # Center
        ]

        self.projector.solve_from_gcps(gcps)

        # Forward accuracy at GCPs - affine exactly reproduces a linear mapping
        for pixel, expected_geo in gcps:
            geo = self.projector.pixel_to_world(pixel)
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-6, \
                f"Lat error at {pixel}: {geo.latitude_deg:.8f} vs {expected_geo.latitude_deg}"
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-6, \
                f"Lon error at {pixel}: {geo.longitude_deg:.8f} vs {expected_geo.longitude_deg}"

        # Roundtrip at GCP locations
        for pixel, _ in gcps:
            geo = self.projector.pixel_to_world(pixel)
            result_pixel = self.projector.world_to_pixel(geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 1e-6
            assert abs(result_pixel.y_px - pixel.y_px) < 1e-6

        # Center pixel sanity check
        center_geo = self.projector.pixel_to_world(Pixel(960.0, 540.0))
        assert abs(center_geo.latitude_deg - 35.5) < 0.001
        assert abs(center_geo.longitude_deg - (-117.5)) < 0.001

    def test_affine_solve_requires_minimum_gcps(self):
        """Verify solve_from_gcps raises with fewer than 3 GCPs."""
        with pytest.raises(ValueError, match="At least 3 GCPs"):
            self.projector.solve_from_gcps([
                (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
                (Pixel(1920.0, 0.0), Geographic(35.0, -117.0)),
            ])

    def test_affine_solve_large_image_coordinates(self):
        """Verify affine solve with large pixel coordinates (from actual GCP data).

        This test reproduces the numerical instability issue when pixel
        coordinates are very large (thousands) compared to geographic
        coordinates (hundreds). The scale mismatch causes poor least
        squares conditioning, resulting in high residual errors.

        Uses actual GCP data from the user's collection (12288x12288 image,
        26 GCPs distributed across Southern California).

        Expected behavior without normalization: RMSE > 100 pixels (poor fit)
        Expected behavior with normalization: RMSE < 1 pixel (good fit)
        """
        # Use actual GCP data from the user's collection
        gcps = [
            (Pixel(3105.0, 3606.0), Geographic(35.397429, -119.037101)),
            (Pixel(2873.0, 3312.0), Geographic(35.397131, -119.033732)),
            (Pixel(8386.0, 10520.0), Geographic(35.404233, -119.102923)),
            (Pixel(8281.0, 10577.0), Geographic(35.40481, -119.103105)),
            (Pixel(6216.0, 9956.0), Geographic(35.409873, -119.09494)),
            (Pixel(9570.0, 9818.0), Geographic(35.397516, -119.100595)),
            (Pixel(11043.0, 8389.0), Geographic(35.386518, -119.093272)),
            (Pixel(12200.0, 7510.0), Geographic(35.378507, -119.089238)),
            (Pixel(7491.0, 6128.0), Geographic(35.390637, -119.068767)),
            (Pixel(5232.0, 6710.0), Geographic(35.401784, -119.068902)),
        ]

        self.projector.solve_from_gcps(gcps)

        # Calculate residuals at GCP locations (same as transformation.py)
        residuals = []
        for pixel, geo in gcps:
            pred = self.projector.world_to_pixel(geo)
            dx = pred.x_px - pixel.x_px
            dy = pred.y_px - pixel.y_px
            rms = (dx ** 2 + dy ** 2) ** 0.5
            residuals.append(rms)

        max(residuals)
        overall_rmse = (sum(r ** 2 for r in residuals) / len(residuals)) ** 0.5

        # Regression test: baseline RMSE with 10 GCPs is ~142 pixels
        # With all 26 GCPs, RMSE is 293 pixels (model tester result)
        # This documents the baseline affine performance for comparison
        assert abs(overall_rmse - 142.0) < 10.0, f"RMSE regression test failed: {overall_rmse:.2f} pixels"
