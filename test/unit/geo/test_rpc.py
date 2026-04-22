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

import numpy as np
import pytest

from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import RPC, Transformation_Type


class TestRPC:
    """Test RPC projector implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = RPC()

        # Sample RPC coefficients (simplified for testing)
        # With (sample, line) arg order:
        #   line_num=[0,0,1] -> 1*line = latitude from line
        #   samp_num=[0,1,0] -> 1*sample = longitude from sample
        self.rpc_coeffs = {
            'line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # lat = line
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # lon = sample
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # line = lat
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # sample = lon
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

    def test_transformation_type(self):
        """Verify RPC projector reports correct transformation type.

        Goal: Ensure the RPC class correctly identifies itself as Transformation_Type.RPC
        for proper dispatcher routing and type checking.
        """
        assert self.projector.transformation_type == Transformation_Type.RPC

    def test_is_identity(self):
        """Verify RPC projector is not an identity transformation.

        Goal: Ensure RPC.is_identity returns False since RPC always involves
        non-trivial polynomial mapping, even with identity-like coefficients.
        """
        assert self.projector.is_identity is False

    def test_update_model(self):
        """Verify RPC coefficient loading and storage.

        Goal: Ensure update_model() correctly parses and stores:
        - Forward RPC coefficients (line_num, line_den, samp_num, samp_den)
        - Inverse RPC coefficients (inv_line_num, inv_line_den, inv_samp_num, inv_samp_den)
        - Normalization parameters (offsets and scales)
        """
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Verify coefficients are set and match input values
        assert self.projector._coeffs is not None
        assert self.projector._offsets is not None
        assert self.projector._scales is not None

        # Verify specific coefficient values were stored correctly
        assert self.projector._coeffs['line_num'] == self.rpc_coeffs['line_num_coefs']
        assert self.projector._coeffs['line_den'] == self.rpc_coeffs['line_den_coefs']
        assert self.projector._coeffs['samp_num'] == self.rpc_coeffs['samp_num_coefs']
        assert self.projector._coeffs['samp_den'] == self.rpc_coeffs['samp_den_coefs']

        # Verify normalization parameters
        assert self.projector._offsets['line_off'] == self.rpc_coeffs['line_offset']
        assert self.projector._offsets['samp_off'] == self.rpc_coeffs['samp_offset']
        assert self.projector._offsets['lat_off'] == self.rpc_coeffs['lat_offset']
        assert self.projector._offsets['lon_off'] == self.rpc_coeffs['lon_offset']
        assert self.projector._scales['line_scale'] == self.rpc_coeffs['line_scale']
        assert self.projector._scales['samp_scale'] == self.rpc_coeffs['samp_scale']
        assert self.projector._scales['lat_scale'] == self.rpc_coeffs['lat_scale']
        assert self.projector._scales['lon_scale'] == self.rpc_coeffs['lon_scale']

    def test_update_model_missing_coeffs(self):
        """Verify error handling when RPC coefficients are not provided.

        Goal: Ensure update_model() raises ValueError with clear message when
        required rpc_coeffs dictionary is missing, preventing silent failures.
        """
        with pytest.raises(ValueError, match="rpc_coeffs required"):
            self.projector.update_model()

    def test_pixel_to_world_no_model(self):
        """Verify error when forward transforming without loaded coefficients.

        Goal: Ensure pixel_to_world() raises ValueError if called before
        update_model(), protecting against undefined behavior.
        """
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            self.projector.pixel_to_world(Pixel(100, 200))

    def test_world_to_pixel_no_model(self):
        """Verify error when inverse transforming without loaded coefficients.

        Goal: Ensure world_to_pixel() raises ValueError if called before
        update_model(), protecting against undefined behavior.
        """
        with pytest.raises(ValueError, match="RPC coefficients not set"):
            self.projector.world_to_pixel(Geographic(35.0, -118.0))

    def test_identity_rpc_transformation(self):
        """Verify 1:1 linear mapping from pixel to geographic coordinates.

        Goal: Test basic forward transformation with identity-like coefficients:
        - pixel.y (line) -> latitude
        - pixel.x (sample) -> longitude
        Validates the fundamental (sample, line) argument order to _compute_polynomial.
        """
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Test pixel to geographic
        pixel = Pixel(100.0, 35.0)  # Use latitude in valid range
        geo = self.projector.pixel_to_world(pixel)

        # With identity coefficients, should be approximately the same
        assert abs(geo.latitude_deg - pixel.y_px) < 1e-6
        assert abs(geo.longitude_deg - pixel.x_px) < 1e-6

    def test_inverse_rpc_transformation(self):
        """Verify 1:1 linear mapping from geographic to pixel coordinates.

        Goal: Test basic inverse transformation with identity-like coefficients:
        - latitude -> line (pixel.y)
        - longitude -> sample (pixel.x)
        Validates inverse polynomial evaluation with (lon, lat) argument order.
        """
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Test geographic to pixel
        geo = Geographic(35.0, 100.0)  # Use valid latitude
        pixel = self.projector.world_to_pixel(geo)

        # With identity coefficients, should be approximately the same
        assert abs(pixel.x_px - geo.longitude_deg) < 1e-6
        assert abs(pixel.y_px - geo.latitude_deg) < 1e-6

    def test_roundtrip_basic(self):
        """Verify pixel -> geographic -> pixel roundtrip with identity coefficients.

        Goal: Test basic roundtrip consistency with simple 1:1 linear mapping:
        original_pixel -> geo -> result_pixel ≈ original_pixel
        This is the simplest possible roundtrip case for validation.
        """
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        original_pixel = Pixel(150.5, 45.0)  # Use valid latitude
        geo = self.projector.pixel_to_world(original_pixel)
        result_pixel = self.projector.world_to_pixel(geo)

        # Should be very close to original
        assert abs(result_pixel.x_px - original_pixel.x_px) < 1e-6
        assert abs(result_pixel.y_px - original_pixel.y_px) < 1e-6

    def test_forward_complex_polynomial(self):
        """Verify forward transformation with non-linear polynomial terms.

        Goal: Test exact polynomial evaluation with cross-terms (x*y) and
        quadratic terms (x²) against analytically hand-computed expected values.
        This validates that _compute_polynomial() evaluates all term types
        correctly, not just linear terms.

        Geographic Scenario:
        - Sensor: pushbroom satellite over Colorado, USA (40N, 105W)
        - Image: 4096x4096 pixels, ~5 degree span (~500km)
        - Distortion model: cross-term (C4*x*y) simulates viewing-angle-dependent
          shift, quadratic (C5*x²) simulates along-track curvature

        Forward polynomials (normalized coordinates nx, ny in [-1, 1]):
          lat_norm = 0.05*nx + 0.5*ny + 0.1*nx*ny + 0.05*nx²
          lon_norm = 0.5*nx + 0.05*ny + 0.05*nx*ny + 0.05*ny²
          lat = lat_norm * 5.0 + 40.0
          lon = lon_norm * 5.0 + (-105.0)

        Note: The inverse of this non-linear system is not a simple polynomial,
        so only forward transformation is tested here against hand-computed values.
        """
        complex_coeffs = {
            # lat_norm = 0.0 + 0.05*nx + 0.5*ny + 0.1*nx*ny + 0.05*nx²
            'line_num_coefs': [0.0, 0.05, 0.5, 0.1, 0.05, 0.0, 0.0, 0.0, 0.0],
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            # lon_norm = 0.0 + 0.5*nx + 0.05*ny + 0.05*nx*ny + 0.0*nx² + 0.05*ny²
            'samp_num_coefs': [0.0, 0.5, 0.05, 0.05, 0.0, 0.05, 0.0, 0.0, 0.0],
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            # Inverse is not tested - non-linear forward has no simple polynomial inverse
            'inv_line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_offset': 2048.0,
            'samp_offset': 2048.0,
            'lat_offset': 40.0,
            'lon_offset': -105.0,
            'line_scale': 2048.0,
            'samp_scale': 2048.0,
            'lat_scale': 5.0,
            'lon_scale': 5.0,
        }

        self.projector.update_model(rpc_coeffs=complex_coeffs)

        # Analytically computed expected values for each test pixel.
        # nx = (x - 2048) / 2048,  ny = (y - 2048) / 2048
        # lat_norm = 0.05*nx + 0.5*ny + 0.1*nx*ny + 0.05*nx²
        # lon_norm = 0.5*nx + 0.05*ny + 0.05*nx*ny + 0.05*ny²
        test_cases = [
            # (pixel, expected_lat, expected_lon)
            # Center: nx=0, ny=0 -> lat_norm=0, lon_norm=0
            (Pixel(2048.0, 2048.0), 40.0, -105.0),
            # Top-left: nx=-1, ny=-1
            # lat_norm = -0.05 - 0.5 + 0.1 + 0.05 = -0.4  -> lat = -0.4*5+40 = 38.0
            # lon_norm = -0.5 - 0.05 + 0.05 + 0.05 = -0.45 -> lon = -0.45*5-105 = -107.25
            (Pixel(0.0, 0.0), 38.0, -107.25),
            # Top-right: nx=1, ny=-1
            # lat_norm = 0.05 - 0.5 - 0.1 + 0.05 = -0.5  -> lat = -0.5*5+40 = 37.5
            # lon_norm = 0.5 - 0.05 - 0.05 + 0.05 = 0.45  -> lon = 0.45*5-105 = -102.75
            (Pixel(4096.0, 0.0), 37.5, -102.75),
            # Bottom-right: nx=1, ny=1
            # lat_norm = 0.05 + 0.5 + 0.1 + 0.05 = 0.7    -> lat = 0.7*5+40 = 43.5
            # lon_norm = 0.5 + 0.05 + 0.05 + 0.05 = 0.65  -> lon = 0.65*5-105 = -101.75
            (Pixel(4096.0, 4096.0), 43.5, -101.75),
            # Interior: nx=-0.5, ny=0.5
            # lat_norm = -0.025 + 0.25 - 0.025 + 0.0125 = 0.2125 -> lat = 0.2125*5+40 = 41.0625
            # lon_norm = -0.25 + 0.025 - 0.0125 + 0.0125 = -0.225 -> lon = -0.225*5-105 = -106.125
            (Pixel(1024.0, 3072.0), 41.0625, -106.125),
        ]

        for pixel, expected_lat, expected_lon in test_cases:
            geo = self.projector.pixel_to_world(pixel)
            assert abs(geo.latitude_deg - expected_lat) < 1e-6, \
                f"Lat error at {pixel}: got {geo.latitude_deg}, expected {expected_lat}"
            assert abs(geo.longitude_deg - expected_lon) < 1e-6, \
                f"Lon error at {pixel}: got {geo.longitude_deg}, expected {expected_lon}"

    def test_complex_rpc_coefficients(self):
        """Verify forward transformation with non-linear polynomial terms.

        Goal: Test that non-zero cross-terms (x*y), quadratic terms (x², y²),
        and higher-order terms are correctly evaluated in forward polynomials.
        Ensures output stays within valid geographic coordinate ranges.
        """
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
        geo = self.projector.pixel_to_world(pixel)

        # Should get reasonable geographic coordinates
        assert -180 <= geo.longitude_deg <= 180
        assert -90 <= geo.latitude_deg <= 90

    def test_polynomial_computation(self):
        """Verify internal polynomial evaluation matches expected math.

        Goal: Test _compute_polynomial() directly against hand-calculated values
        for the GeoTIFF RPC00B term order:
        P = C1 + C2*x + C3*y + C4*x*y + C5*x² + C6*y² + C7*x²*y + C8*x*y² + C9*x²*y²
        """
        self.projector.update_model(rpc_coeffs=self.rpc_coeffs)

        # Test polynomial computation
        result = self.projector._compute_polynomial(0.5, 0.5, [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])

        # Manual calculation for verification
        x, y = 0.5, 0.5
        expected = (1.0 + 2.0*x + 3.0*y + 4.0*x*y + 5.0*x*x + 6.0*y*y +
                   7.0*x*x*y + 8.0*x*y*y + 9.0*x*x*y*y)

        assert abs(result - expected) < 1e-10

    def test_rpc_identity_equivalent(self):
        """Verify scaled/offset linear mapping with normalization parameters.

        Goal: Test complete RPC workflow with offsets and scales:
        - 1024x1024 image centered at pixel (512, 512)
        - Geographic center at (35°N, 118°W) with 10° span
        - Validates forward, inverse, and roundtrip transformations
        Tests real-world scenario where pixel coordinates don't match degrees.
        """
        # Identity RPC: normalized coordinates map directly to geographic
        # With (sample, line) arg order for forward and (lon, lat) for inverse:
        identity_coeffs = {
            'line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # lat = line
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # lon = sample
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_line_num_coefs': [0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # line = lat
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
            'inv_samp_num_coefs': [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # sample = lon
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
            geo = self.projector.pixel_to_world(pixel)
            assert abs(geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
            assert abs(geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

            # Inverse transformation
            result_pixel = self.projector.world_to_pixel(expected_geo)
            assert abs(result_pixel.x_px - pixel.x_px) < 1e-6
            assert abs(result_pixel.y_px - pixel.y_px) < 1e-6

            # Roundtrip verification
            roundtrip_geo = self.projector.pixel_to_world(result_pixel)
            assert abs(roundtrip_geo.latitude_deg - expected_geo.latitude_deg) < 1e-6
            assert abs(roundtrip_geo.longitude_deg - expected_geo.longitude_deg) < 1e-6

    def test_rpc_geographic_coverage(self):
        """Verify RPC with realistic satellite image dimensions and coverage.

        Goal: Test RPC behavior with large image dimensions (4096x4096 pixels)
        and geographic coverage (~5° at 40°N, 105°W, Colorado area).

        This validates:
        - Proper handling of large pixel coordinate ranges
        - Geographic coordinate generation within valid ranges
        - GCP-based verification at multiple image locations
        - Interpolation between control points

        Note: Uses simplified linear coefficients since RPC solver is not yet implemented.
        """
        # Create realistic GCPs for a 4096x4096 satellite image
        # Simulating a pushbroom sensor with slight geometric distortion
        np.random.seed(42)  # Reproducible results

        # Base geographic coverage: 5 degrees
        lat_center, lon_center = 40.0, -105.0
        lat_span, lon_span = 5.0, 5.0

        # Create GCPs at image corners and interior points
        # Format: (pixel, geographic)
        gcp_pixels = [
            # Corners
            Pixel(0.0, 0.0),           # Top-left
            Pixel(4096.0, 0.0),        # Top-right
            Pixel(0.0, 4096.0),        # Bottom-left
            Pixel(4096.0, 4096.0),     # Bottom-right
            # Edge midpoints
            Pixel(2048.0, 0.0),        # Top-center
            Pixel(2048.0, 4096.0),     # Bottom-center
            Pixel(0.0, 2048.0),        # Left-center
            Pixel(4096.0, 2048.0),     # Right-center
            # Interior points
            Pixel(1024.0, 1024.0),
            Pixel(3072.0, 1024.0),
            Pixel(1024.0, 3072.0),
            Pixel(3072.0, 3072.0),
            Pixel(2048.0, 2048.0),     # Center
        ]

        # Generate corresponding geographic coordinates
        # with slight distortion to simulate real sensor geometry
        gcp_geos = []
        for pixel in gcp_pixels:
            # Normalize to [-1, 1]
            nx = (pixel.x_px - 2048.0) / 2048.0
            ny = (pixel.y_px - 2048.0) / 2048.0

            # Base linear mapping (no distortion for simpler test)
            lat = lat_center + lat_span * 0.5 * ny
            lon = lon_center + lon_span * 0.5 * nx

            gcp_geos.append(Geographic(latitude_deg=lat, longitude_deg=lon))

        control_points = list(zip(gcp_pixels, gcp_geos, strict=False))

        # Use linear mapping coefficients (pure linear, no distortion)
        # lat = 40 + 2.5*ny -> normalized_lat = 0.5*ny
        # lon = -105 + 2.5*nx -> normalized_lon = 0.5*nx
        fallback_coeffs = {
            'line_num_coefs': [0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # lat = 0.5*ny
            'line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'samp_num_coefs': [0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # lon = 0.5*nx
            'samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            # Inverse: undo the forward (ny = 2*lat_norm, nx = 2*lon_norm)
            'inv_line_num_coefs': [0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_line_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_num_coefs': [0.0, 2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'inv_samp_den_coefs': [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'line_offset': 2048.0, 'samp_offset': 2048.0,
            'lat_offset': 40.0, 'lon_offset': -105.0,
            'line_scale': 2048.0, 'samp_scale': 2048.0,
            'lat_scale': 5.0, 'lon_scale': 5.0,
        }
        self.projector.update_model(rpc_coeffs=fallback_coeffs)

        # Test 1: Verify exact reconstruction at GCPs
        for pixel, expected_geo in control_points:
            geo = self.projector.pixel_to_world(pixel)

            # At GCPs, forward error should be very small (sub-pixel equivalent in degrees)
            lat_error = abs(geo.latitude_deg - expected_geo.latitude_deg)
            lon_error = abs(geo.longitude_deg - expected_geo.longitude_deg)

            # 0.001 degrees ≈ 100m, which is reasonable for RPC fitting
            assert lat_error < 0.001, f"GCP latitude error {lat_error} for pixel {pixel}"
            assert lon_error < 0.001, f"GCP longitude error {lon_error} for pixel {pixel}"

        # Test 2: Verify interpolation at interior points
        test_pixels = [
            Pixel(1536.0, 1536.0),   # Between GCPs
            Pixel(2560.0, 2560.0),   # Between GCPs
            Pixel(512.0, 3584.0),    # Near edge
        ]

        for pixel in test_pixels:
            geo = self.projector.pixel_to_world(pixel)

            # Verify coordinates are reasonable (within expected range)
            assert 37.0 <= geo.latitude_deg <= 43.0, f"Interpolated lat {geo.latitude_deg} out of range for {pixel}"
            assert -108.0 <= geo.longitude_deg <= -102.0, f"Interpolated lon {geo.longitude_deg} out of range for {pixel}"

        # Test 3: Basic sanity check - center pixel should give center coordinates
        center_pixel = Pixel(2048.0, 2048.0)
        center_geo = self.projector.pixel_to_world(center_pixel)

        # Center should be near (40.0, -105.0) within 0.01 degrees (~1km)
        assert abs(center_geo.latitude_deg - 40.0) < 0.01
        assert abs(center_geo.longitude_deg - (-105.0)) < 0.01

    def test_rpc_gcp_solve_bidirectional(self):
        """Verify solve_from_gcps() produces a bidirectional model for a natural scene.

        Goal: Test the full GCP -> solve -> forward/inverse workflow:
        1. Create realistic GCPs for a Colorado valley scene with mild distortion
        2. Call solve_from_gcps() to fit both forward and inverse polynomials
        3. Verify forward accuracy at GCP locations (sub-0.001 degree)
        4. Verify roundtrip (pixel -> geo -> pixel) accuracy (sub-pixel)

        Geographic Scenario:
        - Scene: Colorado valley, sensor at nadir, mild off-axis viewing distortion
        - Image: 4096x4096 pixels, center at (2048, 2048)
        - Coverage: 40N +/-2.5deg lat, 105W +/-2.5deg lon (~500km square)
        - Distortion: mild cross-term (C4 = 0.05) simulating sensor row-dependent
          scale variation, typical in pushbroom imagery with slight yaw error

        True mapping (used to generate GCPs):
          lat = 40.0 + 2.5 * (ny + 0.05 * nx * ny)
          lon = -105.0 + 2.5 * (nx + 0.05 * nx * ny)

        The cross-term produces ~0.125 degree (~14km) shift at image corners,
        a realistic magnitude for a low-accuracy model.

        Solver approach: least-squares fit of 9-term polynomial (denominator=1)
        to 25 GCPs (5x5 grid). The true mapping uses only 3 terms so the
        solver has enough degrees of freedom to fit it exactly.
        """
        # Generate 25 GCPs in a 5x5 grid using the known true mapping
        image_center_x, image_center_y = 2048.0, 2048.0
        image_half_size = 2048.0

        lat_center, lon_center = 40.0, -105.0
        geo_half_span = 2.5  # degrees

        gcps = []
        grid_steps = np.linspace(-1.0, 1.0, 5)  # nx, ny values: -1, -0.5, 0, 0.5, 1

        for nx_val in grid_steps:
            for ny_val in grid_steps:
                pixel_x = image_center_x + nx_val * image_half_size
                pixel_y = image_center_y + ny_val * image_half_size

                # True mapping: linear + mild cross-term
                lat = lat_center + geo_half_span * (ny_val + 0.05 * nx_val * ny_val)
                lon = lon_center + geo_half_span * (nx_val + 0.05 * nx_val * ny_val)

                gcps.append((Pixel(pixel_x, pixel_y), Geographic(latitude_deg=lat, longitude_deg=lon)))

        # Solve forward and inverse polynomials from GCPs
        self.projector.solve_from_gcps(gcps)

        # Test 1: Forward accuracy at each GCP location
        for pixel, expected_geo in gcps:
            geo = self.projector.pixel_to_world(pixel)
            lat_err = abs(geo.latitude_deg - expected_geo.latitude_deg)
            lon_err = abs(geo.longitude_deg - expected_geo.longitude_deg)

            assert lat_err < 0.001, \
                f"Forward lat error {lat_err:.6f} deg at pixel {pixel}"
            assert lon_err < 0.001, \
                f"Forward lon error {lon_err:.6f} deg at pixel {pixel}"

        # Test 2: Roundtrip - pixel -> geo -> pixel at GCP locations
        for original_pixel, _ in gcps:
            geo = self.projector.pixel_to_world(original_pixel)
            recovered_pixel = self.projector.world_to_pixel(geo)

            x_err = abs(recovered_pixel.x_px - original_pixel.x_px)
            y_err = abs(recovered_pixel.y_px - original_pixel.y_px)

            assert x_err < 1.0, \
                f"Roundtrip x error {x_err:.4f} px at pixel {original_pixel}"
            assert y_err < 1.0, \
                f"Roundtrip y error {y_err:.4f} px at pixel {original_pixel}"

        # Test 3: Center pixel sanity check - center should map near scene center
        center_geo = self.projector.pixel_to_world(Pixel(2048.0, 2048.0))
        assert abs(center_geo.latitude_deg - lat_center) < 0.01
        assert abs(center_geo.longitude_deg - lon_center) < 0.01
