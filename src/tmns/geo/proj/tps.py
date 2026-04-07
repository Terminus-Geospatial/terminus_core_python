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
#    File:    tps.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
TPS (Thin Plate Spline) projector implementation

Thin Plate Spline is a non-parametric interpolation method that minimizes bending energy
while passing exactly through all control points. It combines:

- Radial basis functions (r² log(r²)) for non-linear warping
- Linear terms (ax + by + c) to handle affine components
- Exact interpolation at control points

Mathematical form:
    f(x, y) = Σᵢ wᵢ φ(||(x, y) - (xᵢ, yᵢ)||²) + a₁x + a₂y + a₃
    where φ(r²) = r² log(r²)

The inverse transformation is approximated using nearest-neighbor local linearization
since the true inverse requires solving a non-linear system iteratively.
"""

# Python Standard Libraries
import math
from typing import List, Tuple

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class TPS(Projector):
    """
    Thin Plate Spline projector for non-linear transformations.

    The TPS interpolates exactly through all provided control points while minimizing
    bending energy. It is well-suited for modeling smooth distortions in satellite imagery
    and for applications requiring precise local control with global smoothness.

    Notes:
    - Forward transformation (pixel → geographic) is exact at control points
    - Inverse transformation (geographic → pixel) uses a simplified nearest-neighbor
      approximation and may have significant error for points far from control points
    - Requires at least 3 non-collinear control points
    - Control points should be well-distributed across the image for best results

    Attributes:
        _control_points: List of (Pixel, Geographic) control point tuples
        _weights_x: Solved radial basis weights for longitude
        _weights_y: Solved radial basis weights for latitude
        _linear_terms_x: Linear affine coefficients for longitude (a₁, a₂, a₃)
        _linear_terms_y: Linear affine coefficients for latitude (a₁, a₂, a₃)
    """

    def __init__(self):
        super().__init__()
        self._control_points: List[Tuple[Pixel, Geographic]] = []
        self._weights_x: np.ndarray | None = None
        self._weights_y: np.ndarray | None = None
        self._linear_terms_x: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._linear_terms_y: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform pixel coordinates to geographic using TPS.

        Args:
            pixel: Source pixel coordinates

        Returns:
            Geographic coordinates computed via TPS interpolation

        Raises:
            ValueError: If model not fitted or no control points available
        """
        if self._weights_x is None or self._weights_y is None:
            raise ValueError("TPS model not fitted. Call update_model() with control points first.")

        n = len(self._control_points)
        if n == 0:
            raise ValueError("No control points available for transformation.")

        # Compute radial basis functions
        r_values = np.zeros(n)
        for i, (control_pixel, _) in enumerate(self._control_points):
            dx = pixel.x_px - control_pixel.x_px
            dy = pixel.y_px - control_pixel.y_px
            r_squared = dx * dx + dy * dy
            if r_squared < 1e-10:
                r_values[i] = 0.0
            else:
                r_values[i] = r_squared * math.log(r_squared)

        # Compute transformed coordinates
        # Linear terms: (constant, x_coeff, y_coeff)
        lon = (np.dot(self._weights_x[:n], r_values) +
               self._linear_terms_x[0] +  # constant term
               self._linear_terms_x[1] * pixel.x_px +  # x coefficient
               self._linear_terms_x[2] * pixel.y_px)   # y coefficient

        lat = (np.dot(self._weights_y[:n], r_values) +
               self._linear_terms_y[0] +  # constant term
               self._linear_terms_y[1] * pixel.x_px +  # x coefficient
               self._linear_terms_y[2] * pixel.y_px)   # y coefficient

        return Geographic(latitude_deg=lat, longitude_deg=lon)

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to pixel using iterative Newton inversion.

        Solves the non-linear TPS inverse by iteratively minimizing the residual
        between the forward TPS output and the target geographic coordinates.
        Uses a numerical Jacobian computed via finite differences.

        Args:
            geo: Geographic coordinates to transform

        Returns:
            Pixel coordinates recovered via Newton iteration

        Raises:
            ValueError: If model not fitted or no control points available
        """
        if self._weights_x is None or self._weights_y is None:
            raise ValueError("TPS model not fitted. Call update_model() with control points first.")

        if not self._control_points:
            raise ValueError("No control points available for inverse transformation.")

        # Initial guess: nearest control point in geographic space
        target_lat = geo.latitude_deg
        target_lon = geo.longitude_deg

        min_dist = float('inf')
        x = 0.0
        y = 0.0
        for cp_pixel, cp_geo in self._control_points:
            dist = ((cp_geo.latitude_deg - target_lat) ** 2 +
                    (cp_geo.longitude_deg - target_lon) ** 2)
            if dist < min_dist:
                min_dist = dist
                x = cp_pixel.x_px
                y = cp_pixel.y_px

        # Newton iteration with numerical Jacobian
        eps = 0.5  # finite difference step in pixels
        max_iters = 50
        tol = 1e-7  # convergence in degrees

        for _ in range(max_iters):
            geo_est = self.source_to_geographic(Pixel(x, y))
            dlat = target_lat - geo_est.latitude_deg
            dlon = target_lon - geo_est.longitude_deg

            if abs(dlat) < tol and abs(dlon) < tol:
                break

            # Numerical Jacobian via forward finite differences
            geo_dx = self.source_to_geographic(Pixel(x + eps, y))
            geo_dy = self.source_to_geographic(Pixel(x, y + eps))

            j00 = (geo_dx.latitude_deg - geo_est.latitude_deg) / eps   # dlat/dx
            j01 = (geo_dy.latitude_deg - geo_est.latitude_deg) / eps   # dlat/dy
            j10 = (geo_dx.longitude_deg - geo_est.longitude_deg) / eps  # dlon/dx
            j11 = (geo_dy.longitude_deg - geo_est.longitude_deg) / eps  # dlon/dy

            det = j00 * j11 - j01 * j10
            if abs(det) < 1e-15:
                break  # Singular Jacobian - cannot converge

            # Newton update: [dx, dy] = J^-1 @ [dlat, dlon]
            x += (j11 * dlat - j01 * dlon) / det
            y += (j00 * dlon - j10 * dlat) / det

        return Pixel(x_px=x, y_px=y)


    def update_model(self, **kwargs) -> None:
        """Fit TPS model to control points.

        Args:
            control_points: List of (Pixel, Geographic) tuples for fitting

        Raises:
            ValueError: If control_points missing, insufficient, or collinear

        Notes:
            - Builds the TPS matrix system with radial basis functions and linear constraints
            - Solves for radial basis weights and affine linear terms
            - Requires at least 3 non-collinear control points
        """
        if 'control_points' not in kwargs:
            raise ValueError("control_points required for TPS projector")

        self._control_points = kwargs['control_points']

        if len(self._control_points) < 3:
            raise ValueError("TPS requires at least 3 control points")

        # Build TPS matrix system
        n = len(self._control_points)
        K = np.zeros((n + 3, n + 3))

        # Fill radial basis function matrix
        for i in range(n):
            for j in range(n):
                dx = self._control_points[i][0].x_px - self._control_points[j][0].x_px
                dy = self._control_points[i][0].y_px - self._control_points[j][0].y_px
                r_squared = dx * dx + dy * dy
                if r_squared < 1e-10:
                    K[i, j] = 0.0
                else:
                    K[i, j] = r_squared * math.log(r_squared)

        # Add linear constraints
        for i in range(n):
            K[i, n] = 1.0
            K[i, n + 1] = self._control_points[i][0].x_px
            K[i, n + 2] = self._control_points[i][0].y_px
            K[n, i] = 1.0
            K[n + 1, i] = self._control_points[i][0].x_px
            K[n + 2, i] = self._control_points[i][0].y_px

        # Target coordinates
        target_lon = np.array([geo.longitude_deg for _, geo in self._control_points] + [0.0, 0.0, 0.0])
        target_lat = np.array([geo.latitude_deg for _, geo in self._control_points] + [0.0, 0.0, 0.0])

        try:
            # Solve for weights
            weights_lon = np.linalg.solve(K, target_lon)
            weights_lat = np.linalg.solve(K, target_lat)

            self._weights_x = weights_lon
            self._weights_y = weights_lat

            # Extract linear terms
            self._linear_terms_x = (weights_lon[n], weights_lon[n + 1], weights_lon[n + 2])
            self._linear_terms_y = (weights_lat[n], weights_lat[n + 1], weights_lat[n + 2])

        except np.linalg.LinAlgError:
            raise ValueError("Failed to solve TPS system - control points may be collinear")

    def _compute_radial_basis(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Compute radial basis function for TPS."""
        dx = x1 - x2
        dy = y1 - y2
        r_squared = dx * dx + dy * dy

        if r_squared < 1e-10:
            return 0.0
        else:
            return r_squared * math.log(r_squared)

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.TPS

    @property
    def is_identity(self) -> bool:
        return False

    def image_bounds(self) -> List[Pixel]:
        """Return image bounding box as 4 corner pixels.

        Derives bounds from control point pixel coordinates.
        """
        if not self._control_points:
            raise ValueError("TPS model not fitted. Call update_model() with control points first.")

        # Find min/max from control points
        min_x = min(cp[0].x_px for cp in self._control_points)
        max_x = max(cp[0].x_px for cp in self._control_points)
        min_y = min(cp[0].y_px for cp in self._control_points)
        max_y = max(cp[0].y_px for cp in self._control_points)

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
