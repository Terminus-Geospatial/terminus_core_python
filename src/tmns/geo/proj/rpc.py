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

This implementation follows the GeoTIFF RPC00B standard and GDAL's RPC
georeferencing model for satellite imagery.

References:
    - GDAL RFC 22: RPC Georeferencing
      https://gdal.org/en/stable/development/rfc/rfc22_rpc.html
    - GDAL RPC Implementation (gdal_rpc.cpp)
      https://github.com/OSGeo/gdal/blob/master/alg/gdal_rpc.cpp
    - GeoTIFF RPC00B Polynomial Term Order
      http://geotiff.maptools.org/rpc_prop.html

The RPC model uses rational polynomial coefficients to transform between
image pixel coordinates (line, sample) and geographic coordinates
(latitude, longitude, height). The transformation uses normalized
coordinates to improve numerical stability.
"""

# Python Standard Libraries
import math
from typing import Dict, List, Tuple

# Third-Party Libraries
import numpy as np

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
        norm_sample = (pixel.x_px - self._offsets['samp_off']) / self._scales['samp_scale']
        norm_line = (pixel.y_px - self._offsets['line_off']) / self._scales['line_scale']

        # Compute latitude and longitude using rational polynomials
        # Line (row) polynomials: compute latitude from normalized coordinates
        # Sample (col) polynomials: compute longitude from normalized coordinates
        # Args: (norm_sample, norm_line) - c2*sample + c3*line
        line_num = self._compute_polynomial(norm_sample, norm_line, self._coeffs['line_num'])
        line_den = self._compute_polynomial(norm_sample, norm_line, self._coeffs['line_den'])
        samp_num = self._compute_polynomial(norm_sample, norm_line, self._coeffs['samp_num'])
        samp_den = self._compute_polynomial(norm_sample, norm_line, self._coeffs['samp_den'])

        # Apply normalization to get actual coordinates
        latitude = (line_num / line_den) * self._scales['lat_scale'] + self._offsets['lat_off']
        longitude = (samp_num / samp_den) * self._scales['lon_scale'] + self._offsets['lon_off']

        return Geographic(latitude_deg=latitude, longitude_deg=longitude)

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to image pixel coordinates using RPC."""
        if not self._coeffs:
            raise ValueError("RPC coefficients not set. Call update_model() first.")

        # Normalize geographic coordinates
        norm_lat = (geo.latitude_deg - self._offsets['lat_off']) / self._scales['lat_scale']
        norm_lon = (geo.longitude_deg - self._offsets['lon_off']) / self._scales['lon_scale']

        # Compute inverse transformation
        # Both polynomial types use (lon, lat) for consistent coefficient semantics
        # inv_line_num=[0,0,0.5] -> 0 + 0*lon + 0.5*lat = 0.5*lat (c2*Y where Y=lat)
        # inv_samp_num=[0,0.333,0] -> 0 + 0.333*lon + 0*lat = 0.333*lon (c1*X where X=lon)
        line_num = self._compute_polynomial(norm_lon, norm_lat, self._coeffs['inv_line_num'])
        line_den = self._compute_polynomial(norm_lon, norm_lat, self._coeffs['inv_line_den'])
        samp_num = self._compute_polynomial(norm_lon, norm_lat, self._coeffs['inv_samp_num'])
        samp_den = self._compute_polynomial(norm_lon, norm_lat, self._coeffs['inv_samp_den'])

        # Apply normalization to get actual pixel coordinates
        line = (line_num / line_den) * self._scales['line_scale'] + self._offsets['line_off']
        sample = (samp_num / samp_den) * self._scales['samp_scale'] + self._offsets['samp_off']

        return Pixel(x_px=sample, y_px=line)


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
        """Compute polynomial value for normalized coordinates using GeoTIFF RPC00B term order.

        Standard RPC00B 20-term cubic polynomial (2D simplified version):
        C1 + C2*x + C3*y + C4*x*y + C5*x^2 + C6*y^2 + C7*x^2*y + C8*x*y^2 + C9*x^2*y^2

        Where for inverse RPC (image -> ground):
        - x = normalized longitude (for line) or normalized sample (for sample)
        - y = normalized latitude (for line) or normalized line (for sample)
        """
        # GeoTIFF RPC00B standard term order (first 9 terms for 2D):
        # Note: This differs from some other RPC implementations
        terms = [
            1.0,                    # C1: constant
            x,                      # C2: x (lon for line/sample poly, sample for...)
            y,                      # C3: y (lat for line/sample poly, line for...)
            x * y,                  # C4: x*y
            x * x,                  # C5: x^2
            y * y,                  # C6: y^2
            x * x * y,              # C7: x^2*y
            x * y * y,              # C8: x*y^2
            x * x * y * y,          # C9: x^2*y^2
        ]

        # Ensure we have enough coefficients
        if len(coeffs) < len(terms):
            coeffs = coeffs + [0.0] * (len(terms) - len(coeffs))

        result = 0.0
        for i, term in enumerate(terms[:len(coeffs)]):
            result += coeffs[i] * term

        return result

    def solve_from_gcps(self, gcps: List[Tuple[Pixel, Geographic]]) -> None:
        """Fit RPC model to Ground Control Points using least squares.

        Solves two separate 9-term polynomial systems:
        - Forward: (norm_sample, norm_line) -> (lat_norm, lon_norm)
        - Inverse: (norm_lon, norm_lat) -> (norm_line, norm_sample)

        Both use denominator=1 (simplified RPC), making each system a
        standard linear least squares problem.

        Args:
            gcps: List of (Pixel, Geographic) ground control point pairs.
                  Requires at least 9 pairs for a 9-term polynomial.

        Raises:
            ValueError: If fewer than 9 GCPs provided or solve fails.
        """
        if len(gcps) < 9:
            raise ValueError(f"At least 9 GCPs required for 9-term polynomial, got {len(gcps)}")

        pixels = [p for p, _ in gcps]
        geos = [g for _, g in gcps]

        # Compute normalization parameters from data extent
        px_xs = [p.x_px for p in pixels]
        px_ys = [p.y_px for p in pixels]
        lats = [g.latitude_deg for g in geos]
        lons = [g.longitude_deg for g in geos]

        samp_off = (max(px_xs) + min(px_xs)) / 2.0
        line_off = (max(px_ys) + min(px_ys)) / 2.0
        samp_scale = (max(px_xs) - min(px_xs)) / 2.0
        line_scale = (max(px_ys) - min(px_ys)) / 2.0
        lat_off = (max(lats) + min(lats)) / 2.0
        lon_off = (max(lons) + min(lons)) / 2.0
        lat_scale = (max(lats) - min(lats)) / 2.0
        lon_scale = (max(lons) - min(lons)) / 2.0

        # Normalize all coordinates
        nx = np.array([(p.x_px - samp_off) / samp_scale for p in pixels])
        ny = np.array([(p.y_px - line_off) / line_scale for p in pixels])
        nlat = np.array([(g.latitude_deg - lat_off) / lat_scale for g in geos])
        nlon = np.array([(g.longitude_deg - lon_off) / lon_scale for g in geos])

        def build_design_matrix(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
            """Build 9-term polynomial design matrix with RPC00B term order."""
            return np.column_stack([
                np.ones(len(xs)),  # C1: constant
                xs,                # C2: x
                ys,                # C3: y
                xs * ys,           # C4: x*y
                xs * xs,           # C5: x²
                ys * ys,           # C6: y²
                xs * xs * ys,      # C7: x²*y
                xs * ys * ys,      # C8: x*y²
                xs * xs * ys * ys, # C9: x²*y²
            ])

        # Solve forward: (nx, ny) -> (lat_norm, lon_norm)
        A_fwd = build_design_matrix(nx, ny)
        c_lat, _, _, _ = np.linalg.lstsq(A_fwd, nlat, rcond=None)
        c_lon, _, _, _ = np.linalg.lstsq(A_fwd, nlon, rcond=None)

        # Solve inverse: (nlon, nlat) -> (ny, nx)
        # Note: inverse polynomial arg order is (x=nlon, y=nlat)
        A_inv = build_design_matrix(nlon, nlat)
        c_line, _, _, _ = np.linalg.lstsq(A_inv, ny, rcond=None)
        c_samp, _, _, _ = np.linalg.lstsq(A_inv, nx, rcond=None)

        self.update_model(rpc_coeffs={
            'line_num_coefs': c_lat.tolist(),
            'line_den_coefs': [1.0] + [0.0] * 8,
            'samp_num_coefs': c_lon.tolist(),
            'samp_den_coefs': [1.0] + [0.0] * 8,
            'inv_line_num_coefs': c_line.tolist(),
            'inv_line_den_coefs': [1.0] + [0.0] * 8,
            'inv_samp_num_coefs': c_samp.tolist(),
            'inv_samp_den_coefs': [1.0] + [0.0] * 8,
            'line_offset': line_off,
            'samp_offset': samp_off,
            'lat_offset': lat_off,
            'lon_offset': lon_off,
            'line_scale': line_scale,
            'samp_scale': samp_scale,
            'lat_scale': lat_scale,
            'lon_scale': lon_scale,
        })

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

    def image_bounds(self) -> List[Pixel]:
        """Return image bounding box as 4 corner pixels.

        Derives image dimensions from normalization parameters:
        - Normalized range is typically [-1, 1]
        - Pixel range = offset ± scale
        """
        if not self._offsets or not self._scales:
            raise ValueError("RPC coefficients not set. Call update_model() first.")

        # Calculate pixel bounds from offset and scale
        # Normalized: (pixel - offset) / scale
        # So pixel = normalized * scale + offset
        # For normalized [-1, 1]: pixel ranges from offset-scale to offset+scale
        min_x = self._offsets['samp_off'] - self._scales['samp_scale']
        max_x = self._offsets['samp_off'] + self._scales['samp_scale']
        min_y = self._offsets['line_off'] - self._scales['line_scale']
        max_y = self._offsets['line_off'] + self._scales['line_scale']

        return [
            Pixel(x_px=min_x, y_px=min_y),  # Top-left
            Pixel(x_px=max_x, y_px=min_y),  # Top-right
            Pixel(x_px=max_x, y_px=max_y),  # Bottom-right
            Pixel(x_px=min_x, y_px=max_y),  # Bottom-left
        ]

    def geographic_bounds(self) -> List[Geographic]:
        """Return geographic bounding polygon vertices.

        Transforms image_bounds corners to geographic coordinates.
        """
        image_corners = self.image_bounds()
        return [self.source_to_geographic(pixel) for pixel in image_corners]
