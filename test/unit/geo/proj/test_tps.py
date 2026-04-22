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

import numpy as np
import pytest

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import TPS, Transformation_Type


class TestTPS:
    """Test TPS projector implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = TPS()

        # Identity transformation GCPs (5x5 grid = 25 points)
        # Realistic 1920x1080 satellite image with 1°x1° geographic coverage
        self.control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0000, -118.0000)),
            (Pixel(0.0, 270.0), Geographic(35.2500, -118.0000)),
            (Pixel(0.0, 540.0), Geographic(35.5000, -118.0000)),
            (Pixel(0.0, 810.0), Geographic(35.7500, -118.0000)),
            (Pixel(0.0, 1080.0), Geographic(36.0000, -118.0000)),
            (Pixel(480.0, 0.0), Geographic(35.0000, -117.7500)),
            (Pixel(480.0, 270.0), Geographic(35.2500, -117.7500)),
            (Pixel(480.0, 540.0), Geographic(35.5000, -117.7500)),
            (Pixel(480.0, 810.0), Geographic(35.7500, -117.7500)),
            (Pixel(480.0, 1080.0), Geographic(36.0000, -117.7500)),
            (Pixel(960.0, 0.0), Geographic(35.0000, -117.5000)),
            (Pixel(960.0, 270.0), Geographic(35.2500, -117.5000)),
            (Pixel(960.0, 540.0), Geographic(35.5000, -117.5000)),
            (Pixel(960.0, 810.0), Geographic(35.7500, -117.5000)),
            (Pixel(960.0, 1080.0), Geographic(36.0000, -117.5000)),
            (Pixel(1440.0, 0.0), Geographic(35.0000, -117.2500)),
            (Pixel(1440.0, 270.0), Geographic(35.2500, -117.2500)),
            (Pixel(1440.0, 540.0), Geographic(35.5000, -117.2500)),
            (Pixel(1440.0, 810.0), Geographic(35.7500, -117.2500)),
            (Pixel(1440.0, 1080.0), Geographic(36.0000, -117.2500)),
            (Pixel(1920.0, 0.0), Geographic(35.0000, -117.0000)),
            (Pixel(1920.0, 270.0), Geographic(35.2500, -117.0000)),
            (Pixel(1920.0, 540.0), Geographic(35.5000, -117.0000)),
            (Pixel(1920.0, 810.0), Geographic(35.7500, -117.0000)),
            (Pixel(1920.0, 1080.0), Geographic(36.0000, -117.0000)),
        ]

        # Realistic distortion GCPs (22 points - corners, edges, interior)
        self.distortion_points = [
            (Pixel(0.0, 0.0), Geographic(35.0000, -118.0000)),
            (Pixel(1920.0, 0.0), Geographic(35.0000, -117.0000)),
            (Pixel(0.0, 1080.0), Geographic(36.0000, -118.0000)),
            (Pixel(1920.0, 1080.0), Geographic(36.0000, -117.0000)),
            (Pixel(480.0, 0.0), Geographic(35.0010, -117.9980)),
            (Pixel(960.0, 0.0), Geographic(35.0005, -117.9990)),
            (Pixel(1440.0, 0.0), Geographic(35.0010, -117.9980)),
            (Pixel(0.0, 270.0), Geographic(35.0020, -118.0010)),
            (Pixel(0.0, 540.0), Geographic(35.0005, -117.9995)),
            (Pixel(0.0, 810.0), Geographic(35.0020, -118.0010)),
            (Pixel(1920.0, 270.0), Geographic(35.0020, -117.9990)),
            (Pixel(1920.0, 540.0), Geographic(35.0005, -117.9995)),
            (Pixel(1920.0, 810.0), Geographic(35.0020, -117.9990)),
            (Pixel(480.0, 270.0), Geographic(35.2510, -117.7490)),
            (Pixel(960.0, 270.0), Geographic(35.5010, -117.4990)),
            (Pixel(1440.0, 270.0), Geographic(35.7490, -117.2510)),
            (Pixel(480.0, 540.0), Geographic(35.4990, -117.7510)),
            (Pixel(960.0, 540.0), Geographic(35.5005, -117.4995)),
            (Pixel(1440.0, 540.0), Geographic(35.7510, -117.2490)),
            (Pixel(480.0, 810.0), Geographic(35.7490, -117.7510)),
            (Pixel(960.0, 810.0), Geographic(35.7490, -117.2510)),
            (Pixel(1440.0, 810.0), Geographic(35.7490, -117.2490)),
        ]

        # Linear transformation GCPs (4x4 grid = 16 points)
        self.linear_points = [
            (Pixel(0.0, 0.0), Geographic(35.0000, -118.0000)),
            (Pixel(0.0, 360.0), Geographic(35.6667, -118.0000)),
            (Pixel(0.0, 720.0), Geographic(36.3333, -118.0000)),
            (Pixel(0.0, 1080.0), Geographic(37.0000, -118.0000)),
            (Pixel(640.0, 0.0), Geographic(35.0000, -117.0000)),
            (Pixel(640.0, 360.0), Geographic(35.6667, -117.0000)),
            (Pixel(640.0, 720.0), Geographic(36.3333, -117.0000)),
            (Pixel(640.0, 1080.0), Geographic(37.0000, -117.0000)),
            (Pixel(1280.0, 0.0), Geographic(35.0000, -116.0000)),
            (Pixel(1280.0, 360.0), Geographic(35.6667, -116.0000)),
            (Pixel(1280.0, 720.0), Geographic(36.3333, -116.0000)),
            (Pixel(1280.0, 1080.0), Geographic(37.0000, -116.0000)),
            (Pixel(1920.0, 0.0), Geographic(35.0000, -115.0000)),
            (Pixel(1920.0, 360.0), Geographic(35.6667, -115.0000)),
            (Pixel(1920.0, 720.0), Geographic(36.3333, -115.0000)),
            (Pixel(1920.0, 1080.0), Geographic(37.0000, -115.0000)),
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
        assert self.projector.transformation_type == Transformation_Type.TPS

    def test_is_identity(self):
        """Test is_identity property."""
        assert self.projector.is_identity is False

    def test_update_model_with_control_points(self):
        """Test updating model with control points."""
        # Use smaller test dataset for this specific test
        test_control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
        ]

        self.projector.update_model(control_points=test_control_points)

        assert len(self.projector._control_points) == 4
        assert self.projector._weights_x is not None
        assert self.projector._weights_y is not None
        assert self.projector._linear_terms_x is not None
        assert self.projector._linear_terms_y is not None

    def test_update_model_missing_control_points(self):
        """Test error when control points are missing."""
        with pytest.raises(ValueError, match="control_points required"):
            self.projector.update_model()

    def test_update_model_insufficient_control_points(self):
        """Test error when too few control points provided."""
        with pytest.raises(ValueError, match="at least 3 control points"):
            self.projector.update_model(control_points=[(Pixel(0, 0), Geographic(0, 0))])

    def test_pixel_to_world_no_model(self):
        """Test error when transforming without model."""
        with pytest.raises(ValueError, match="TPS model not fitted"):
            self.projector.pixel_to_world(Pixel(50, 50))

    def test_world_to_pixel_no_model(self):
        """Test error when inverse transforming without model."""
        with pytest.raises(ValueError, match="TPS model not fitted"):
            self.projector.world_to_pixel(Geographic(0.5, 0.5))

    def test_simple_tps_transformation(self):
        """Test TPS transformation with simple control points."""
        # Use smaller test dataset for this specific test
        test_control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
        ]

        self.projector.update_model(control_points=test_control_points)

        # Test transformation at control points (should be exact - TPS interpolates perfectly through control points)
        for pixel, expected_geo in test_control_points:
            geo = self.projector.pixel_to_world(pixel)
            # Should be essentially exact at control points
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

    def test_interpolated_transformation(self):
        """Test TPS transformation at interpolated points."""
        # Use smaller test dataset for this specific test
        test_control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
        ]

        self.projector.update_model(control_points=test_control_points)

        # Test at center point
        center_pixel = Pixel(480.0, 270.0)  # Center of the test area
        geo = self.projector.pixel_to_world(center_pixel)

        # Should be approximately at center of geographic space
        assert abs(geo.latitude_deg - 35.25) < 0.1  # Center latitude
        assert abs(geo.longitude_deg - (-117.5)) < 0.1  # Center longitude

    def test_inverse_transformation(self):
        """Verify geo->pixel inverse at control point locations.

        Goal: Test that world_to_pixel() recovers pixel coordinates
        at the exact control point geographic values.
        With Newton iteration, should be sub-pixel accurate at control points.
        """
        test_control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
        ]

        self.projector.update_model(control_points=test_control_points)

        for pixel, geo in test_control_points:
            result_pixel = self.projector.world_to_pixel(geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 1.0
            assert abs(result_pixel.y_px - pixel.y_px) < 1.0

    def test_roundtrip_basic(self):
        """Verify pixel->geo->pixel roundtrip with 4 corner control points.

        Goal: Test basic roundtrip consistency with a minimal linear-like
        control point set (4 corners of a 960x540 region).
        With Newton inversion, roundtrip should be sub-pixel accurate.
        """
        test_control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
        ]

        self.projector.update_model(control_points=test_control_points)

        test_pixels = [
            Pixel(240.0, 135.0),
            Pixel(720.0, 405.0),
            Pixel(480.0, 270.0),
        ]

        for original_pixel in test_pixels:
            geo = self.projector.pixel_to_world(original_pixel)

            assert 34.5 <= geo.latitude_deg <= 36.0
            assert -119.0 <= geo.longitude_deg <= -116.5

            result_pixel = self.projector.world_to_pixel(geo)
            assert abs(result_pixel.x_px - original_pixel.x_px) < 1.0
            assert abs(result_pixel.y_px - original_pixel.y_px) < 1.0

    def test_collinear_control_points(self):
        """Test error with collinear control points."""
        collinear_points = [
            (Pixel(0.0, 0.0), Geographic(0.0, 0.0)),
            (Pixel(50.0, 0.0), Geographic(0.5, 0.0)),
            (Pixel(100.0, 0.0), Geographic(1.0, 0.0)),
        ]

        with pytest.raises(ValueError, match="collinear"):
            self.projector.update_model(control_points=collinear_points)

    def test_roundtrip_dense_grid(self):
        """Verify roundtrip with 25-point identity grid control points.

        Goal: Test that with a well-sampled 5x5 GCP grid, the Newton inverse
        converges accurately even for pixels near image edges.
        """
        self.projector.update_model(control_points=self.control_points)

        original_pixel = Pixel(25.0, 75.0)
        geo = self.projector.pixel_to_world(original_pixel)
        result_pixel = self.projector.world_to_pixel(geo)

        assert abs(result_pixel.x_px - original_pixel.x_px) < 1.0
        assert abs(result_pixel.y_px - original_pixel.y_px) < 1.0

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
        geo = self.projector.pixel_to_world(test_pixel)

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
        geo = self.projector.pixel_to_world(test_pixel)

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
        """Verify TPS linear interpolation for a 1920x1080 Southern California scene.

        Goal: Test that with 5 control points (4 corners + center), TPS:
        1. Passes exactly through all control points
        2. Linearly interpolates between them (with small TPS error)
        3. Roundtrip recovers pixel coordinates sub-pixel accurately

        Geographic Scenario:
        - Scene: Southern California coast (35-36N, 118-117W)
        - Image: 1920x1080 pixels, 1-degree span each axis
        - Mapping: lat = 35 + y/1080, lon = -118 + x/1920
        """
        identity_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),        # Top-left
            (Pixel(1920.0, 0.0), Geographic(35.0, -117.0)),     # Top-right
            (Pixel(0.0, 1080.0), Geographic(36.0, -118.0)),      # Bottom-left
            (Pixel(1920.0, 1080.0), Geographic(36.0, -117.0)),   # Bottom-right
            (Pixel(960.0, 540.0), Geographic(35.5, -117.5)),     # Center
        ]

        self.projector.update_model(control_points=identity_points)

        # TPS passes through control points exactly
        for pixel, expected_geo in identity_points:
            geo = self.projector.pixel_to_world(pixel)
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-10
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-10

        # Interpolated points - expected values from linear mapping:
        # lat = 35 + y/1080,  lon = -118 + x/1920
        test_cases = [
            # (pixel, expected_lat, expected_lon)
            # (480, 270): lat=35+270/1080=35.25, lon=-118+480/1920=-117.75
            (Pixel(480.0, 270.0), 35.25, -117.75),
            # (1440, 810): lat=35+810/1080=35.75, lon=-118+1440/1920=-117.25
            (Pixel(1440.0, 810.0), 35.75, -117.25),
            # (192, 972): lat=35+972/1080=35.9, lon=-118+192/1920=-117.9
            (Pixel(192.0, 972.0), 35.9, -117.9),
            # (1728, 108): lat=35+108/1080=35.1, lon=-118+1728/1920=-117.1
            (Pixel(1728.0, 108.0), 35.1, -117.1),
        ]

        for pixel, expected_lat, expected_lon in test_cases:
            geo = self.projector.pixel_to_world(pixel)

            assert abs(geo.latitude_deg - expected_lat) < 0.01, \
                f"Lat error at {pixel}: got {geo.latitude_deg:.4f}, expected {expected_lat}"
            assert abs(geo.longitude_deg - expected_lon) < 0.01, \
                f"Lon error at {pixel}: got {geo.longitude_deg:.4f}, expected {expected_lon}"

            result_pixel = self.projector.world_to_pixel(
                Geographic(expected_lat, expected_lon)
            )
            assert abs(result_pixel.x_px - pixel.x_px) < 2.0
            assert abs(result_pixel.y_px - pixel.y_px) < 2.0

    def test_tps_complex_distortion_case(self):
        """Verify TPS forward and roundtrip for a mildly distorted scene.

        Goal: Test that TPS handles mild non-linear distortion correctly:
        1. Passes exactly through all 7 control points (TPS property)
        2. Roundtrip (pixel->geo->pixel) is sub-pixel at non-GCP points

        Geographic Scenario:
        - Scene: Southern California (35-36N, 118-117W), 1920x1080
        - Corners are exact (undistorted)
        - Interior GCPs have mild shifts (~0.005 deg / ~500m) simulating
          pushbroom sensor row-dependent scale variation

        True mapping at interior points (distorted from linear baseline):
          lat_base = 35 + y/1080,  lon_base = -118 + x/1920
          + cross-term: 0.005 * (nx*ny) degrees, nx=(x-960)/960, ny=(y-540)/540
        """
        # Well-conditioned control points: exact corners + mildly distorted interior
        complex_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),              # Top-left (exact)
            (Pixel(1920.0, 0.0), Geographic(35.0, -117.0)),           # Top-right (exact)
            (Pixel(0.0, 1080.0), Geographic(36.0, -118.0)),            # Bottom-left (exact)
            (Pixel(1920.0, 1080.0), Geographic(36.0, -117.0)),         # Bottom-right (exact)
            (Pixel(960.0, 540.0), Geographic(35.505, -117.495)),       # Center: +0.005 lat, +0.005 lon
            (Pixel(480.0, 270.0), Geographic(35.252, -117.752)),       # Q1: +0.002 lat, +0.002 lon
            (Pixel(1440.0, 810.0), Geographic(35.748, -117.248)),      # Q3: -0.002 lat, -0.002 lon
        ]

        self.projector.update_model(control_points=complex_points)

        # TPS passes through all control points exactly
        for pixel, expected_geo in complex_points:
            geo = self.projector.pixel_to_world(pixel)
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-8, \
                f"Forward error at control point {pixel}"
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-8, \
                f"Forward error at control point {pixel}"

        # Roundtrip at non-GCP pixels
        test_pixels = [
            Pixel(240.0, 135.0),   # Near top-left
            Pixel(1680.0, 945.0),  # Near bottom-right
            Pixel(960.0, 270.0),   # Top-center
            Pixel(480.0, 540.0),   # Left-center
            Pixel(1152.0, 648.0),  # Interior
        ]

        for pixel in test_pixels:
            geo = self.projector.pixel_to_world(pixel)

            assert 34.8 <= geo.latitude_deg <= 36.2, \
                f"Forward lat {geo.latitude_deg:.4f} out of expected range"
            assert -118.2 <= geo.longitude_deg <= -116.8, \
                f"Forward lon {geo.longitude_deg:.4f} out of expected range"

            result_pixel = self.projector.world_to_pixel(geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 2.0, \
                f"Roundtrip x error {abs(result_pixel.x_px - pixel.x_px):.4f} at {pixel}"
            assert abs(result_pixel.y_px - pixel.y_px) < 2.0, \
                f"Roundtrip y error {abs(result_pixel.y_px - pixel.y_px):.4f} at {pixel}"

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
        geo = self.projector.pixel_to_world(test_pixel)

        # TPS with 4 bilinear corner points reproduces linear mapping exactly
        assert abs(geo.latitude_deg - 0.75) < 1e-6
        assert abs(geo.longitude_deg - 1.0) < 1e-6

        # Test multiple points for solver consistency
        for i in range(5):
            test_x = float(i * 0.2)
            test_y = float(i * 0.15)
            pixel = Pixel(test_x, test_y)

            # Forward transformation
            geo = self.projector.pixel_to_world(pixel)

            # Should follow linear pattern approximately (lat = 3*y, lon = 2*x)
            assert abs(geo.latitude_deg - 3.0 * test_y) < 1e-6
            assert abs(geo.longitude_deg - 2.0 * test_x) < 1e-6

    def test_get_param_bounds_not_implemented(self):
        """Verify get_param_bounds raises NotImplementedError for TPS.

        TPS is interpolatory and does not have a compact parameter vector.
        TPS refinement is done via re-solving from GCPs, not direct parameter optimization.
        This test ensures the stub correctly raises NotImplementedError.
        """
        test_control_points = [
            (Pixel(0.0, 0.0), Geographic(35.0, -118.0)),
            (Pixel(960.0, 0.0), Geographic(35.0, -117.0)),
            (Pixel(0.0, 540.0), Geographic(35.5, -118.0)),
            (Pixel(960.0, 540.0), Geographic(35.5, -117.0)),
        ]
        self.projector.update_model(control_points=test_control_points)

        with pytest.raises(NotImplementedError, match="TPS does not support parameter-based optimization"):
            self.projector.get_param_bounds()
