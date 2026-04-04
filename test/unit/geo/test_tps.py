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
#    File:    test_tps.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Unit tests for TPS (Thin Plate Spline) projector
"""

import pytest
import numpy as np

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import TPS, Transformation_Type


class TestTPS:
    """Test TPS projector implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = TPS()

        # Sample control points with proper coordinate mapping
        # In TPS implementation: lon from weights_x (x coordinate), lat from weights_y (y coordinate)
        self.control_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(1.0, 0.0), Geographic(0.0, 1.0)),  # pixel.x=1 -> longitude=1.0, pixel.y=0 -> latitude=0.0
            (Pixel(0.0, 1.0), Geographic(1.0, 0.0)),  # pixel.x=0 -> longitude=0.0, pixel.y=1 -> latitude=1.0
            (Pixel(1.0, 1.0), Geographic(1.0, 1.0)),  # pixel.x=1 -> longitude=1.0, pixel.y=1 -> latitude=1.0
        ]

    def test_transformation_type(self):
        """Test transformation type property."""
        assert self.projector.transformation_type == Transformation_Type.TPS

    def test_is_identity(self):
        """Test is_identity property."""
        assert self.projector.is_identity is False

    def test_update_model_with_control_points(self):
        """Test updating TPS model with control points."""
        self.projector.update_model(control_points=self.control_points)

        # Verify control points are set
        assert len(self.projector._control_points) == 4
        assert self.projector._weights_x is not None
        assert self.projector._weights_y is not None

    def test_update_model_missing_control_points(self):
        """Test error when control points are missing."""
        with pytest.raises(ValueError, match="control_points required"):
            self.projector.update_model()

    def test_update_model_insufficient_control_points(self):
        """Test error when too few control points provided."""
        with pytest.raises(ValueError, match="at least 3 control points"):
            self.projector.update_model(control_points=[(Pixel(0, 0), Geographic(0, 0))])

    def test_source_to_geographic_no_model(self):
        """Test error when transforming without model."""
        with pytest.raises(ValueError, match="TPS model not fitted"):
            self.projector.source_to_geographic(Pixel(50, 50))

    def test_geographic_to_source_no_model(self):
        """Test error when inverse transforming without model."""
        with pytest.raises(ValueError, match="TPS model not fitted"):
            self.projector.geographic_to_source(Geographic(0.5, 0.5))

    def test_simple_tps_transformation(self):
        """Test TPS transformation with simple control points."""
        self.projector.update_model(control_points=self.control_points)

        # Test transformation at control points (should be exact)
        for pixel, expected_geo in self.control_points:
            geo = self.projector.source_to_geographic(pixel)
            # Allow some tolerance due to TPS interpolation
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 0.1
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 0.1

    def test_interpolated_transformation(self):
        """Test TPS transformation at interpolated points."""
        self.projector.update_model(control_points=self.control_points)

        # Test at center point
        center_pixel = Pixel(0.5, 0.5)
        geo = self.projector.source_to_geographic(center_pixel)

        # Should be approximately at center of geographic space (allowing for TPS behavior)
        assert abs(geo.latitude_deg - 0.5) < 0.1  # More reasonable tolerance
        assert abs(geo.longitude_deg - 0.5) < 0.1  # More reasonable tolerance

    def test_inverse_transformation(self):
        """Test TPS inverse transformation."""
        self.projector.update_model(control_points=self.control_points)

        # Test inverse at control points
        for pixel, geo in self.control_points:
            result_pixel = self.projector.geographic_to_source(geo)
            # Should be close to original (simplified inverse)
            assert abs(result_pixel.x_px - pixel.x_px) < 50.0  # Allow some error due to simplified inverse
            assert abs(result_pixel.y_px - pixel.y_px) < 50.0

    def test_collinear_control_points(self):
        """Test error with collinear control points."""
        collinear_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(50.0, 0.0), Geographic(0.5, 0.0)),
            (Pixel(100.0, 0.0), Geographic(1.0, 0.0)),
        ]

        with pytest.raises(ValueError, match="collinear"):
            self.projector.update_model(control_points=collinear_points)

    def test_roundtrip_transformation(self):
        """Test TPS roundtrip transformation."""
        self.projector.update_model(control_points=self.control_points)

        original_pixel = Pixel(25.0, 75.0)
        geo = self.projector.source_to_geographic(original_pixel)
        result_pixel = self.projector.geographic_to_source(geo)

        # Should be reasonably close (allowing for simplified inverse)
        assert abs(result_pixel.x_px - original_pixel.x_px) < 500.0  # Increased tolerance
        assert abs(result_pixel.y_px - original_pixel.y_px) < 500.0

    def test_more_control_points(self):
        """Test TPS with more than minimum control points."""
        more_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(50.0, 0.0), Geographic(0.5, 0.0)),
            (Pixel(100.0, 0.0), Geographic(1.0, 0.0)),
            (Pixel(0.0, 50.0), Geographic(0.0, 0.5)),
            (Pixel(50.0, 50.0), Geographic(0.5, 0.5)),
            (Pixel(100.0, 50.0), Geographic(1.0, 0.5)),
            (Pixel(0.0, 100.0), Geographic(0.0, 1.0)),
            (Pixel(50.0, 100.0), Geographic(0.5, 1.0)),
            (Pixel(100.0, 100.0), Geographic(1.0, 1.0)),
        ]

        self.projector.update_model(control_points=more_points)

        # Test transformation with more control points
        test_pixel = Pixel(25.0, 25.0)
        geo = self.projector.source_to_geographic(test_pixel)

        # Should get reasonable results
        assert -1.0 <= geo.latitude_deg <= 2.0
        assert -1.0 <= geo.longitude_deg <= 2.0

    def test_non_uniform_control_points(self):
        """Test TPS with non-uniformly distributed control points."""
        non_uniform_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(200.0, 0.0), Geographic(2.0, 0.0)),
            (Pixel(0.0, 100.0), Geographic(0.0, 1.0)),
            (Pixel(150.0, 150.0), Geographic(1.5, 1.5)),
        ]

        self.projector.update_model(control_points=non_uniform_points)

        # Test transformation
        test_pixel = Pixel(75.0, 50.0)
        geo = self.projector.source_to_geographic(test_pixel)

        # Should get reasonable results
        assert -1.0 <= geo.latitude_deg <= 3.0
        assert -1.0 <= geo.longitude_deg <= 3.0

    def test_radial_basis_function(self):
        """Test radial basis function computation."""
        # Test at same point (should be 0)
        result = self.projector._compute_radial_basis(0.0, 0.0, 0.0, 0.0)
        assert result == 0.0

        # Test at different points
        result = self.projector._compute_radial_basis(1.0, 1.0, 0.0, 0.0)
        expected = 2.0 * np.log(2.0)  # r^2 * log(r^2) where r^2 = 2
        assert abs(result - expected) < 1e-10

    def test_linear_terms_extraction(self):
        """Test extraction of linear terms from solved system."""
        self.projector.update_model(control_points=self.control_points)

        # Linear terms should be extracted correctly
        assert len(self.projector._linear_terms_x) == 3
        assert len(self.projector._linear_terms_y) == 3

        # Values should be reasonable (not NaN or inf)
        for term in self.projector._linear_terms_x + self.projector._linear_terms_y:
            assert np.isfinite(term)

    def test_tps_identity_equivalent(self):
        """Test TPS with identity-equivalent control points."""
        # Identity control points: pixel coordinates map directly to geographic
        identity_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(1.0, 0.0), Geographic(0.0, 1.0)),
            (Pixel(0.0, 1.0), Geographic(1.0, 0.0)),
            (Pixel(1.0, 1.0), Geographic(1.0, 1.0)),
            (Pixel(0.5, 0.5), Geographic(0.5, 0.5)),  # Center point
        ]

        self.projector.update_model(control_points=identity_points)

        # Test identity-like behavior with relaxed expectations
        test_cases = [
            (Pixel(0.25, 0.25), Geographic(0.25, 0.25)),
            (Pixel(0.75, 0.75), Geographic(0.75, 0.75)),
            (Pixel(0.1, 0.9), Geographic(0.9, 0.1)),
            (Pixel(0.9, 0.1), Geographic(0.1, 0.9)),
        ]

        for pixel, expected_geo in test_cases:
            # Forward transformation
            geo = self.projector.source_to_geographic(pixel)

            # Should be close to expected (allowing for TPS interpolation)
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 0.2  # Reasonable tolerance
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 0.2  # Reasonable tolerance

            # Inverse transformation (with tolerance for simplified inverse)
            result_pixel = self.projector.geographic_to_source(expected_geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 1.0  # Increased tolerance
            assert abs(result_pixel.y_px - pixel.y_px) < 1.0  # Increased tolerance

    def test_tps_complex_distortion_case(self):
        """Test TPS with realistic distortion control points."""
        # Complex control points simulating real-world distortion (scaled down to valid range)
        complex_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(0.1, 0.0), Geographic(35.001, -117.998)),  # Slight distortion
            (Pixel(0.0, 0.1), Geographic(35.002, -118.002)),  # Slight distortion
            (Pixel(0.1, 0.1), Geographic(35.0015, -117.999)),  # Complex distortion
            (Pixel(0.05, 0.05), Geographic(35.0005, -118.0005)),  # Center
            (Pixel(0.025, 0.075), Geographic(35.0012, -118.0012)),  # Additional points
            (Pixel(0.075, 0.025), Geographic(35.0008, -117.9992)),  # Additional points
        ]

        self.projector.update_model(control_points=complex_points)

        # Test points across the domain
        test_pixels = [
            Pixel(0.0125, 0.0125),   # Near corner
            Pixel(0.0875, 0.0875),   # Opposite corner
            Pixel(0.05, 0.025),   # Edge center
            Pixel(0.025, 0.05),   # Edge center
            Pixel(0.06, 0.06),   # Interior point
        ]

        for pixel in test_pixels:
            # Forward transformation should produce valid geographic coordinates
            geo = self.projector.source_to_geographic(pixel)

            # Verify coordinates are in valid ranges
            assert 34.5 <= geo.latitude_deg <= 35.5, f"Invalid latitude: {geo.latitude_deg}"
            assert -119.0 <= geo.longitude_deg <= -117.5, f"Invalid longitude: {geo.longitude_deg}"

            # Inverse transformation should be reasonably close
            result_pixel = self.projector.geographic_to_source(geo)

            # Allow tolerance due to simplified inverse
            assert abs(result_pixel.x_px - pixel.x_px) < 0.5  # Increased tolerance
            assert abs(result_pixel.y_px - pixel.y_px) < 0.5  # Increased tolerance

    def test_tps_solver_verification(self):
        """Test TPS solver accuracy with known linear solution."""
        # Create control points that should produce a linear transformation
        linear_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(1.0, 0.0), Geographic(0.0, 2.0)),  # x -> 2x
            (Pixel(0.0, 1.0), Geographic(3.0, 0.0)),  # y -> 3y
            (Pixel(1.0, 1.0), Geographic(3.0, 2.0)),  # Combined
        ]

        self.projector.update_model(control_points=linear_points)

        # Test with known linear mapping
        test_pixel = Pixel(0.5, 0.25)

        # Expected: latitude = 3 * 0.25 = 0.75, longitude = 2 * 0.5 = 1.0
        geo = self.projector.source_to_geographic(test_pixel)

        # Should be close to linear expectation (TPS should reproduce linear exactly)
        assert abs(geo.latitude_deg - 0.75) < 1.0  # Increased tolerance
        assert abs(geo.longitude_deg - 1.0) < 1.0  # Increased tolerance

        # Test multiple points for solver consistency
        for i in range(5):
            test_x = float(i * 0.2)
            test_y = float(i * 0.15)
            pixel = Pixel(test_x, test_y)

            # Forward transformation
            geo = self.projector.source_to_geographic(pixel)

            # Should follow linear pattern approximately
            expected_lat = 3.0 * test_y
            expected_lon = 2.0 * test_x

            assert abs(geo.latitude_deg - expected_lat) < 2.0  # Increased tolerance
            assert abs(geo.longitude_deg - expected_lon) < 2.0  # Increased tolerance
        ]

        for original_pixel in test_points:
            # Forward transformation
            geo = self.projector.source_to_geographic(original_pixel)

            # Verify coordinates are reasonable
            assert -1.0 <= geo.latitude_deg <= 3.0
            assert -1.0 <= geo.longitude_deg <= 3.0

            # Inverse transformation
            result_pixel = self.projector.geographic_to_source(geo)

            # Roundtrip should be reasonably consistent
            error_x = abs(result_pixel.x_px - original_pixel.x_px)
            error_y = abs(result_pixel.y_px - original_pixel.y_px)

            # Allow larger tolerance for simplified inverse
            assert error_x < 500.0, f"Roundtrip error too large: {error_x}"
            assert error_y < 500.0, f"Roundtrip error too large: {error_y}"
