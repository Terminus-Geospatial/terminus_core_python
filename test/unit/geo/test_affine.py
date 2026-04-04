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
Unit tests for Affine projector
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
        """Test transformation type property."""
        assert self.projector.transformation_type == Transformation_Type.AFFINE

    def test_is_identity(self):
        """Test is_identity property."""
        assert self.projector.is_identity is False

    def test_update_model(self):
        """Test updating the transformation model."""
        self.projector.update_model(transform_matrix=self.translation_matrix)
        assert self.projector._transform_matrix == self.translation_matrix
        assert self.projector._inverse_matrix is not None

    def test_uninitialized_model_raises_error(self):
        """Test that uninitialized model raises appropriate errors."""
        with pytest.raises(ValueError, match="Transform matrix not set"):
            self.projector.source_to_geographic(Pixel(x_px=0, y_px=0))

    def test_translation_transformation(self):
        """Test simple translation transformation."""
        self.projector.update_model(transform_matrix=self.translation_matrix)

        # Test source to geographic - use valid coordinate ranges
        pixel = Pixel(x_px=35.0, y_px=-80.0)  # Use valid latitude range
        geo = self.projector.source_to_geographic(pixel)

        assert abs(geo.latitude_deg - (-79.99)) < 1e-10  # y: -80 + (-0.01) = -79.99
        assert abs(geo.longitude_deg - 35.01) < 1e-10  # x: 35 + 0.01 = 35.01

        # Test inverse transformation
        result_pixel = self.projector.geographic_to_source(geo)
        assert result_pixel.x_px == 35.0
        assert result_pixel.y_px == -80.0

    def test_scaling_transformation(self):
        """Test simple scaling transformation."""
        self.projector.update_model(transform_matrix=self.scaling_matrix)

        # Test source to geographic - use small coordinates to stay in range
        pixel = Pixel(x_px=30.0, y_px=-50.0)  # Use valid range
        geo = self.projector.source_to_geographic(pixel)

        assert geo.latitude_deg == -45.0  # y: -50 * 0.9 = -45.0
        assert geo.longitude_deg == 33.0  # x: 30 * 1.1 = 33.0

        # Test inverse transformation
        result_pixel = self.projector.geographic_to_source(geo)
        assert result_pixel.x_px == 30.0
        assert result_pixel.y_px == -50.0

    def test_complex_transformation(self):
        """Test complex transformation with rotation and scaling."""
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
        geo = self.projector.source_to_geographic(original_pixel)
        result_pixel = self.projector.geographic_to_source(geo)

        # Should be very close to original (allowing for floating point error)
        assert abs(result_pixel.x_px - original_pixel.x_px) < 1e-10
        assert abs(result_pixel.y_px - original_pixel.y_px) < 1e-10

    def test_singular_matrix_raises_error(self):
        """Test that singular matrix raises appropriate error."""
        singular_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 0.0],  # This makes the matrix singular
            [0.0, 0.0, 1.0]
        ]

        with pytest.raises(ValueError, match="Singular transformation matrix"):
            self.projector.update_model(transform_matrix=singular_matrix)

    def test_destination_transformation(self):
        """Test that destination transformations work the same as source."""
        self.projector.update_model(transform_matrix=self.translation_matrix)

        pixel = Pixel(x_px=50.0, y_px=75.0)
        geo = self.projector.destination_to_geographic(pixel)
        result_pixel = self.projector.geographic_to_destination(geo)

        assert result_pixel.x_px == 50.0
        assert result_pixel.y_px == 75.0

    def test_roundtrip_precision(self):
        """Test roundtrip transformation precision."""
        self.projector.update_model(transform_matrix=self.scaling_matrix)

        # Test multiple roundtrips with small coordinates
        original_pixel = Pixel(x_px=35.123, y_px=-50.456)  # Use valid coordinates

        for _ in range(10):
            geo = self.projector.source_to_geographic(original_pixel)
            original_pixel = self.projector.geographic_to_source(geo)

        # Should maintain precision
        assert abs(original_pixel.x_px - 35.123) < 1e-10
        assert abs(original_pixel.y_px - -50.456) < 1e-10

    def test_matrix_inverse_computation(self):
        """Test that matrix inverse is computed correctly."""
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
        """Test edge cases and boundary conditions."""
        # Test with identity matrix
        identity_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]

        self.projector.update_model(transform_matrix=identity_matrix)

        # Should behave like identity transformation
        pixel = Pixel(x_px=45.0, y_px=-90.0)  # Use valid coordinates
        geo = self.projector.source_to_geographic(pixel)

        assert abs(geo.latitude_deg - pixel.y_px) < 1e-10  # latitude comes from y
        assert abs(geo.longitude_deg - pixel.x_px) < 1e-10  # longitude comes from x

    def test_large_coordinate_values(self):
        """Test with large coordinate values."""
        # Use matrix that keeps coordinates in valid range
        small_scale_matrix = [
            [0.001, 0.0, 0.0],
            [0.0, 0.001, 0.0],
            [0.0, 0.0, 1.0]
        ]

        self.projector.update_model(transform_matrix=small_scale_matrix)

        # Test with large pixel coordinates
        pixel = Pixel(x_px=50000.0, y_px=80000.0)
        geo = self.projector.source_to_geographic(pixel)

        # Should be scaled down to valid range
        assert -90 <= geo.latitude_deg <= 90
        assert -180 <= geo.longitude_deg <= 180

        # Roundtrip should work
        result_pixel = self.projector.geographic_to_source(geo)
        assert abs(result_pixel.x_px - pixel.x_px) < 1e-6
        assert abs(result_pixel.y_px - pixel.y_px) < 1e-6
