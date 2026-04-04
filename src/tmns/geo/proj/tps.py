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
    """Thin Plate Spline projector for non-linear transformations."""

    def __init__(self):
        super().__init__()
        self._control_points: List[Tuple[Pixel, Geographic]] = []
        self._weights_x: np.ndarray | None = None
        self._weights_y: np.ndarray | None = None
        self._linear_terms_x: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._linear_terms_y: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform pixel coordinates to geographic using TPS."""
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
        lon = (np.dot(self._weights_x[:n], r_values) +
               self._linear_terms_x[0] * pixel.x_px +
               self._linear_terms_x[1] * pixel.y_px +
               self._linear_terms_x[2])

        lat = (np.dot(self._weights_y[:n], r_values) +
               self._linear_terms_y[0] * pixel.x_px +
               self._linear_terms_y[1] * pixel.y_px +
               self._linear_terms_y[2])

        return Geographic(latitude_deg=lat, longitude_deg=lon)

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to pixel using inverse TPS."""
        # Note: True TPS inverse requires solving a system of equations
        # For simplicity, we'll use a basic approach with iteration
        if self._weights_x is None or self._weights_y is None:
            raise ValueError("TPS model not fitted. Call update_model() with control points first.")

        # Simple approach: find closest control point and use local approximation
        min_dist = float('inf')
        closest_pixel = None
        closest_geo = None

        for control_pixel, control_geo in self._control_points:
            dist = math.sqrt((geo.latitude_deg - control_geo.latitude_deg)**2 +
                           (geo.longitude_deg - control_geo.longitude_deg)**2)
            if dist < min_dist:
                min_dist = dist
                closest_pixel = control_pixel
                closest_geo = control_geo

        if closest_pixel is None:
            raise ValueError("No control points available for inverse transformation.")

        # Simple linear approximation around closest point
        # In a real implementation, this would use iterative solving
        dx = geo.longitude_deg - closest_geo.longitude_deg
        dy = geo.latitude_deg - closest_geo.latitude_deg

        # Approximate inverse (this is simplified)
        pixel_x = closest_pixel.x_px + dx * 1000  # Rough scale factor
        pixel_y = closest_pixel.y_px + dy * 1000

        return Pixel(x_px=pixel_x, y_px=pixel_y)

    def destination_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform destination pixel to geographic (same as source for TPS)."""
        return self.source_to_geographic(pixel)

    def geographic_to_destination(self, geo: Geographic) -> Pixel:
        """Transform geographic to destination pixel (same as source for TPS)."""
        return self.geographic_to_source(geo)

    def update_model(self, **kwargs) -> None:
        """Fit TPS model to control points."""
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
