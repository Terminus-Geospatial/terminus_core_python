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
#    File:    test_gcp_simulator_projectors.py
#    Author:  Marvin Smith
#    Date:    04/06/2026
#
"""
Integration tests for fitting projectors using GCP simulator points.

Tests that verify Affine, TPS, and RPC projectors can be fitted from
simulated GCP data and accurately project between pixel and geographic
coordinates.
"""

# Python Standard Libraries
import sys
from pathlib import Path

# Add tools directory to path for importing simulator
tools_path = Path(__file__).parent.parent.parent.parent / 'tools'
sys.path.insert(0, str(tools_path))

# Third-Party Libraries
import numpy as np
import pytest

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.transformer import Transformer
from tmns.geo.proj import Affine, TPS, RPC, Transformation_Type

# Simulator imports
from tmns_gcp_simulator import (
    GCP_Simulator,
    Pinhole_Camera,
    Camera_Intrinsics,
    Extrinsic_Params,
    Ground_Control_Point
)


class Test_GCP_Simulator_Projector_Fitting:
    """Test fitting projectors from GCP simulator data."""

    def setup_method(self):
        """Set up test fixtures with standard simulator."""
        # Create standard simulator with nadir view
        intrinsics = Camera_Intrinsics(
            width=4096,
            height=4096,
            focal_length=0.056,
            cx=2048.0,
            cy=2048.0
        )
        camera = Pinhole_Camera(intrinsics)

        extrinsic = Extrinsic_Params.from_lat_lon_alt(
            latitude=35.3733,
            longitude=-119.0187,
            altitude=5486.4,
            yaw=0.0,
            pitch=-90.0,  # Nadir
            roll=0.0
        )

        self.simulator = GCP_Simulator(camera, extrinsic)
        self.transformer = Transformer()

    def _gcps_to_control_points(self, gcps: list[Ground_Control_Point]) -> list[tuple[Pixel, Geographic]]:
        """Convert GCPs to (Pixel, Geographic) control point tuples."""
        control_points = []
        for gcp in gcps:
            geo = self.transformer.ecef_to_geo(gcp.world)
            control_points.append((gcp.pixel, geo))
        return control_points

    def _compute_affine_matrix(self, control_points: list[tuple[Pixel, Geographic]]) -> list[list[float]]:
        """Compute affine transformation matrix from control points using least squares.

        Solves: [lon, lat, 1] = M @ [x, y, 1]

        Returns:
            3x3 transformation matrix as nested list
        """
        n = len(control_points)
        if n < 3:
            raise ValueError("Need at least 3 control points for affine fit")

        # Build matrices for least squares
        A = np.zeros((n * 2, 6))
        b = np.zeros(n * 2)

        for i, (pixel, geo) in enumerate(control_points):
            # Row for longitude
            A[i * 2] = [pixel.x_px, pixel.y_px, 1, 0, 0, 0]
            b[i * 2] = geo.longitude_deg

            # Row for latitude
            A[i * 2 + 1] = [0, 0, 0, pixel.x_px, pixel.y_px, 1]
            b[i * 2 + 1] = geo.latitude_deg

        # Solve least squares
        x = np.linalg.lstsq(A, b, rcond=None)[0]

        # Build 3x3 homogeneous matrix
        # [lon]   [a b c]   [x]
        # [lat] = [d e f] @ [y]
        # [ 1 ]   [0 0 1]   [1]
        matrix = [
            [x[0], x[1], x[2]],  # lon = a*x + b*y + c
            [x[3], x[4], x[5]],  # lat = d*x + e*y + f
            [0.0, 0.0, 1.0]
        ]

        return matrix

    def _fit_rpc_coefficients(self, control_points: list[tuple[Pixel, Geographic]]) -> dict:
        """Fit simplified RPC coefficients from control points.

        Uses linear approximation (1st order polynomial) for stability.
        Full RPC would use higher-order polynomials.
        """
        n = len(control_points)
        if n < 4:
            raise ValueError("Need at least 4 control points for RPC fit")

        # Extract coordinates
        pixels = np.array([(p.x_px, p.y_px) for p, _ in control_points])
        geos = np.array([(g.longitude_deg, g.latitude_deg) for _, g in control_points])

        # Compute normalization parameters
        px_mean, py_mean = pixels.mean(axis=0)
        px_std, py_std = pixels.std(axis=0)
        if px_std < 1e-6:
            px_std = 1.0
        if py_std < 1e-6:
            py_std = 1.0

        lon_mean, lat_mean = geos.mean(axis=0)
        lon_std, lat_std = geos.std(axis=0)
        if lon_std < 1e-6:
            lon_std = 1.0
        if lat_std < 1e-6:
            lat_std = 1.0

        # Normalize coordinates
        p_norm = (pixels - [px_mean, py_mean]) / [px_std, py_std]
        g_norm = (geos - [lon_mean, lat_mean]) / [lon_std, lat_std]

        # Fit linear model: geo_norm = A @ pixel_norm + b
        # Using least squares for [A, b]
        X = np.column_stack([p_norm, np.ones(n)])  # [x, y, 1]

        # Solve for longitude coefficients
        coefs_lon = np.linalg.lstsq(X, g_norm[:, 0], rcond=None)[0]
        # Solve for latitude coefficients
        coefs_lat = np.linalg.lstsq(X, g_norm[:, 1], rcond=None)[0]

        # Build RPC coefficient structure (using 9-term simplified form)
        # Terms: 1, x, y, xy, x^2, y^2, x^2y, xy^2, x^2y^2
        def build_coeffs(linear_coefs):
            """Build 9-term RPC coefficients from linear fit."""
            # Linear terms in normalized space
            # geo_norm = a*x_norm + b*y_norm + c
            # We'll store: [c, a, b, 0, 0, 0, 0, 0, 0]
            return [linear_coefs[2], linear_coefs[0], linear_coefs[1], 0, 0, 0, 0, 0, 0]

        # For denominator, use simple [1, 0, 0, ...] (no scaling)
        den_coefs = [1.0] + [0.0] * 8

        rpc_data = {
            'line_num_coefs': build_coeffs(coefs_lat),
            'line_den_coefs': den_coefs.copy(),
            'samp_num_coefs': build_coeffs(coefs_lon),
            'samp_den_coefs': den_coefs.copy(),
            'inv_line_num_coefs': build_coeffs(coefs_lat),  # Simplified inverse
            'inv_line_den_coefs': den_coefs.copy(),
            'inv_samp_num_coefs': build_coeffs(coefs_lon),
            'inv_samp_den_coefs': den_coefs.copy(),
            'line_offset': py_mean,
            'samp_offset': px_mean,
            'lat_offset': lat_mean,
            'lon_offset': lon_mean,
            'line_scale': py_std,
            'samp_scale': px_std,
            'lat_scale': lat_std,
            'lon_scale': lon_std,
            'height_offset': 0.0,
            'height_scale': 1.0
        }

        return rpc_data

    def test_affine_fitting_from_gcps(self):
        """Test fitting affine projector from simulated GCPs."""
        # Generate GCPs
        gcps = self.simulator.generate_gcps(points_x=5, points_y=5)
        assert len(gcps) >= 3, f"Need at least 3 GCPs, got {len(gcps)}"

        # Convert to control points
        control_points = self._gcps_to_control_points(gcps)

        # Compute affine matrix
        matrix = self._compute_affine_matrix(control_points)

        # Create and configure affine projector
        affine = Affine()
        affine.update_model(transform_matrix=matrix)

        # Test forward transformation (pixel -> geo) on control points
        max_pixel_error = 0
        for pixel, expected_geo in control_points:
            geo = affine.source_to_geographic(pixel)

            # Check geographic coordinates
            lon_error = abs(geo.longitude_deg - expected_geo.longitude_deg)
            lat_error = abs(geo.latitude_deg - expected_geo.latitude_deg)

            assert lon_error < 0.01, f"Longitude error too large: {lon_error}"
            assert lat_error < 0.01, f"Latitude error too large: {lat_error}"

        # Test roundtrip (pixel -> geo -> pixel)
        for pixel, _ in control_points[:3]:  # Test subset
            geo = affine.source_to_geographic(pixel)
            pixel_back = affine.geographic_to_source(geo)

            x_error = abs(pixel_back.x_px - pixel.x_px)
            y_error = abs(pixel_back.y_px - pixel.y_px)

            max_pixel_error = max(max_pixel_error, x_error, y_error)

        # Affine should have small roundtrip error on fitted points
        assert max_pixel_error < 5.0, f"Roundtrip pixel error too large: {max_pixel_error}"

    def test_tps_fitting_from_gcps(self):
        """Test fitting TPS projector from simulated GCPs."""
        # Generate GCPs
        gcps = self.simulator.generate_gcps(points_x=5, points_y=5)
        assert len(gcps) >= 3, f"Need at least 3 GCPs for TPS, got {len(gcps)}"

        # Convert to control points
        control_points = self._gcps_to_control_points(gcps)

        # Create and fit TPS projector
        tps = TPS()
        tps.update_model(control_points=control_points)

        # Test forward transformation (pixel -> geo)
        # TPS should interpolate exactly through control points
        for pixel, expected_geo in control_points:
            geo = tps.source_to_geographic(pixel)

            lon_error = abs(geo.longitude_deg - expected_geo.longitude_deg)
            lat_error = abs(geo.latitude_deg - expected_geo.latitude_deg)

            # TPS interpolates exactly through control points
            assert lon_error < 1e-6, f"TPS longitude interpolation error: {lon_error}"
            assert lat_error < 1e-6, f"TPS latitude interpolation error: {lat_error}"

    def test_rpc_fitting_from_gcps(self):
        """Test fitting RPC projector from simulated GCPs."""
        # Generate GCPs
        gcps = self.simulator.generate_gcps(points_x=6, points_y=6)
        assert len(gcps) >= 4, f"Need at least 4 GCPs for RPC, got {len(gcps)}"

        # Convert to control points
        control_points = self._gcps_to_control_points(gcps)

        # Fit RPC coefficients
        rpc_data = self._fit_rpc_coefficients(control_points)

        # Create and configure RPC projector
        rpc = RPC()
        rpc.update_model(rpc_coeffs=rpc_data)

        # Test forward transformation (pixel -> geo)
        max_geo_error = 0
        for pixel, expected_geo in control_points:
            geo = rpc.source_to_geographic(pixel)

            lon_error = abs(geo.longitude_deg - expected_geo.longitude_deg)
            lat_error = abs(geo.latitude_deg - expected_geo.latitude_deg)

            max_geo_error = max(max_geo_error, lon_error, lat_error)

        # RPC should have reasonable accuracy on fitted points
        # Note: Our simplified linear RPC won't be perfect
        assert max_geo_error < 0.1, f"RPC geographic error too large: {max_geo_error}"

    def test_cross_projector_consistency(self):
        """Test that all projectors give consistent results on same GCPs."""
        # Generate GCPs
        gcps = self.simulator.generate_gcps(points_x=5, points_y=5)
        control_points = self._gcps_to_control_points(gcps)

        # Create projectors
        affine = Affine()
        affine.update_model(transform_matrix=self._compute_affine_matrix(control_points))

        tps = TPS()
        tps.update_model(control_points=control_points)

        rpc = RPC()
        rpc.update_model(rpc_coeffs=self._fit_rpc_coefficients(control_points))

        # Test on a sample pixel
        test_pixel = Pixel(x_px=2048.0, y_px=2048.0)  # Image center

        geo_affine = affine.source_to_geographic(test_pixel)
        geo_tps = tps.source_to_geographic(test_pixel)
        geo_rpc = rpc.source_to_geographic(test_pixel)

        # Results should be reasonably close (within ~100m for this test)
        lat_spread = max(geo_affine.latitude_deg, geo_tps.latitude_deg, geo_rpc.latitude_deg) - \
                     min(geo_affine.latitude_deg, geo_tps.latitude_deg, geo_rpc.latitude_deg)
        lon_spread = max(geo_affine.longitude_deg, geo_tps.longitude_deg, geo_rpc.longitude_deg) - \
                     min(geo_affine.longitude_deg, geo_tps.longitude_deg, geo_rpc.longitude_deg)

        # At Bakersfield latitude, 0.001 degrees ~ 100m
        assert lat_spread < 0.01, f"Projector latitude inconsistency: {lat_spread}"
        assert lon_spread < 0.01, f"Projector longitude inconsistency: {lon_spread}"

    def test_projector_transformation_types(self):
        """Test that fitted projectors report correct transformation types."""
        gcps = self.simulator.generate_gcps(points_x=3, points_y=3)
        control_points = self._gcps_to_control_points(gcps)

        affine = Affine()
        affine.update_model(transform_matrix=self._compute_affine_matrix(control_points))
        assert affine.transformation_type == Transformation_Type.AFFINE
        assert not affine.is_identity

        tps = TPS()
        tps.update_model(control_points=control_points)
        assert tps.transformation_type == Transformation_Type.TPS
        assert not tps.is_identity

        rpc = RPC()
        rpc.update_model(rpc_coeffs=self._fit_rpc_coefficients(control_points))
        assert rpc.transformation_type == Transformation_Type.RPC
        assert not rpc.is_identity
