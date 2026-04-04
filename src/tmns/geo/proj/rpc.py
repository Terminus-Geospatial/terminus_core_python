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
#    File:    rpc.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
RPC (Rational Polynomial Coefficients) projector implementation
"""

# Python Standard Libraries
import math
from typing import List, Tuple

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class RPC(Projector):
    """Rational Polynomial Coefficients (RPC) projector for satellite imagery."""

    def __init__(self):
        super().__init__()
        self._coeffs: Dict[str, List[float]] = {}
        self._offsets: Dict[str, float] = {}
        self._scales: Dict[str, float] = {}

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform image pixel coordinates to geographic coordinates using RPC."""
        if not self._coeffs:
            raise ValueError("RPC coefficients not set. Call update_model() first.")

        # Normalize pixel coordinates
        norm_x = (pixel.x_px - self._offsets['samp_off']) / self._scales['samp_scale']
        norm_y = (pixel.y_px - self._offsets['line_off']) / self._scales['line_scale']

        # Compute row and latitude using rational polynomials
        row_num = self._compute_polynomial(norm_x, norm_y, self._coeffs['line_num'])
        row_den = self._compute_polynomial(norm_x, norm_y, self._coeffs['line_den'])
        col_num = self._compute_polynomial(norm_x, norm_y, self._coeffs['samp_num'])
        col_den = self._compute_polynomial(norm_x, norm_y, self._coeffs['samp_den'])

        # Apply normalization to get actual coordinates
        latitude = (row_num / row_den) * self._scales['lat_scale'] + self._offsets['lat_off']
        longitude = (col_num / col_den) * self._scales['lon_scale'] + self._offsets['lon_off']

        return Geographic(latitude_deg=latitude, longitude_deg=longitude)

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to image pixel coordinates using RPC."""
        if not self._coeffs:
            raise ValueError("RPC coefficients not set. Call update_model() first.")

        # Normalize geographic coordinates
        norm_lat = (geo.latitude_deg - self._offsets['lat_off']) / self._scales['lat_scale']
        norm_lon = (geo.longitude_deg - self._offsets['lon_off']) / self._scales['lon_scale']

        # Compute inverse transformation (using simplified approach)
        # Note: True RPC inverse requires iterative solving
        line_num = self._compute_polynomial(norm_lat, norm_lon, self._coeffs['inv_line_num'])
        line_den = self._compute_polynomial(norm_lat, norm_lon, self._coeffs['inv_line_den'])
        samp_num = self._compute_polynomial(norm_lat, norm_lon, self._coeffs['inv_samp_num'])
        samp_den = self._compute_polynomial(norm_lat, norm_lon, self._coeffs['inv_samp_den'])

        # Apply normalization to get actual pixel coordinates
        line = (line_num / line_den) * self._scales['line_scale'] + self._offsets['line_off']
        sample = (samp_num / samp_den) * self._scales['samp_scale'] + self._offsets['samp_off']

        return Pixel(x_px=sample, y_px=line)

    def destination_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform destination pixel to geographic (same as source for RPC)."""
        return self.source_to_geographic(pixel)

    def geographic_to_destination(self, geo: Geographic) -> Pixel:
        """Transform geographic to destination pixel (same as source for RPC)."""
        return self.geographic_to_source(geo)

    def update_model(self, **kwargs) -> None:
        """Update RPC coefficients and normalization parameters."""
        if 'rpc_coeffs' not in kwargs:
            raise ValueError("rpc_coeffs required for RPC projector")

        rpc_data = kwargs['rpc_coeffs']
        
        # Extract coefficients
        self._coeffs = {
            'line_num': rpc_data['line_num_coefs'],
            'line_den': rpc_data['line_den_coefs'],
            'samp_num': rpc_data['samp_num_coefs'],
            'samp_den': rpc_data['samp_den_coefs'],
            'inv_line_num': rpc_data.get('inv_line_num_coefs', self._generate_default_coeffs()),
            'inv_line_den': rpc_data.get('inv_line_den_coefs', self._generate_default_coeffs()),
            'inv_samp_num': rpc_data.get('inv_samp_num_coefs', self._generate_default_coeffs()),
            'inv_samp_den': rpc_data.get('inv_samp_den_coefs', self._generate_default_coeffs()),
        }

        # Extract normalization parameters
        self._offsets = {
            'line_off': rpc_data['line_offset'],
            'samp_off': rpc_data['samp_offset'],
            'lat_off': rpc_data['lat_offset'],
            'lon_off': rpc_data['lon_offset'],
            'height_off': rpc_data.get('height_offset', 0.0),
        }

        self._scales = {
            'line_scale': rpc_data['line_scale'],
            'samp_scale': rpc_data['samp_scale'],
            'lat_scale': rpc_data['lat_scale'],
            'lon_scale': rpc_data['lon_scale'],
            'height_scale': rpc_data.get('height_scale', 1.0),
        }

    def _compute_polynomial(self, x: float, y: float, coeffs: List[float]) -> float:
        """Compute polynomial value for normalized coordinates."""
        # RPC polynomial terms: [1, x, y, x*y, x^2, y^2, x^2*y, x*y^2, x^3, y^3, x^3*y, x*y^3, x^2*y^2, x^3*y^2, x^2*y^3, x^3*y^3, x^2*y^3, x^3*y^2, x^4, y^4]
        # For simplicity, we'll use first 9 terms (typical RPC order)
        terms = [
            1.0,                    # constant
            x,                      # x
            y,                      # y
            x * y,                  # xy
            x * x,                  # x^2
            y * y,                  # y^2
            x * x * y,              # x^2y
            x * y * y,              # xy^2
            x * x * y * y,          # x^2y^2
        ]

        # Ensure we have enough coefficients
        if len(coeffs) < len(terms):
            coeffs = coeffs + [0.0] * (len(terms) - len(coeffs))

        result = 0.0
        for i, term in enumerate(terms[:len(coeffs)]):
            result += coeffs[i] * term

        return result

    def _generate_default_coeffs(self) -> List[float]:
        """Generate default coefficients for missing inverse RPC."""
        # Simple identity-like coefficients
        return [0.0] * 20  # 20 coefficients for full RPC polynomial

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.RPC

    @property
    def is_identity(self) -> bool:
        return False
