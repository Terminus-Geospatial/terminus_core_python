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
#    File:    affine.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Affine projector implementation
"""

# Python Standard Libraries
from typing import List

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class Affine(Projector):
    """Affine transformation using transformation matrix."""

    def __init__(self):
        super().__init__()
        self._transform_matrix: List[List[float]] | None = None
        self._inverse_matrix: List[List[float]] | None = None

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform source pixel to geographic using affine matrix."""
        if self._transform_matrix is None:
            raise ValueError("Transform matrix not set. Call update_model() first.")

        # Apply affine transformation: [x', y', 1] = M * [x, y, 1]
        x_prime = (self._transform_matrix[0][0] * pixel.x_px +
                  self._transform_matrix[0][1] * pixel.y_px +
                  self._transform_matrix[0][2])
        y_prime = (self._transform_matrix[1][0] * pixel.x_px +
                  self._transform_matrix[1][1] * pixel.y_px +
                  self._transform_matrix[1][2])

        return Geographic(latitude_deg=y_prime, longitude_deg=x_prime)

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic to source pixel using inverse affine matrix."""
        if self._inverse_matrix is None:
            raise ValueError("Inverse matrix not set. Call update_model() first.")

        # Apply inverse transformation: [x, y, 1] = M_inv * [x', y', 1]
        x = (self._inverse_matrix[0][0] * geo.longitude_deg +
             self._inverse_matrix[0][1] * geo.latitude_deg +
             self._inverse_matrix[0][2])
        y = (self._inverse_matrix[1][0] * geo.longitude_deg +
             self._inverse_matrix[1][1] * geo.latitude_deg +
             self._inverse_matrix[1][2])

        return Pixel(x_px=x, y_px=y)

    def destination_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform destination pixel to geographic (same as source for affine)."""
        return self.source_to_geographic(pixel)

    def geographic_to_destination(self, geo: Geographic) -> Pixel:
        """Transform geographic to destination pixel (same as source for affine)."""
        return self.geographic_to_source(geo)

    def update_model(self, **kwargs) -> None:
        """Update the affine transformation matrix."""
        if 'transform_matrix' not in kwargs:
            raise ValueError("transform_matrix required for affine projector")

        self._transform_matrix = kwargs['transform_matrix']
        self._inverse_matrix = self._compute_inverse_matrix(self._transform_matrix)

    def _compute_inverse_matrix(self, matrix: List[List[float]]) -> List[List[float]]:
        """Compute the inverse of a 3x3 affine transformation matrix."""
        # Extract 2x2 transformation part and translation
        a, b, c = matrix[0]
        d, e, f = matrix[1]
        
        # Compute determinant of 2x2 part
        det = a * e - b * d
        if abs(det) < 1e-10:
            raise ValueError("Singular transformation matrix (determinant near zero)")

        # Compute inverse of 2x2 part
        a_inv = e / det
        b_inv = -b / det
        c_inv = (b * f - c * e) / det
        d_inv = -d / det
        e_inv = a / det
        f_inv = (c * d - a * f) / det

        return [
            [a_inv, b_inv, c_inv],
            [d_inv, e_inv, f_inv],
            [0.0, 0.0, 1.0]
        ]

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.AFFINE

    @property
    def is_identity(self) -> bool:
        return False
