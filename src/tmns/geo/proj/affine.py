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

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class Affine(Projector):
    """Affine projector - 3x3 homogeneous affine transformation.

    Matrix convention
    -----------------
    ``M @ [x, y, 1]^T = [lon, lat, 1]^T``

    Row 0 defines the longitude polynomial, row 1 defines latitude::

        lon = M[0,0]*x + M[0,1]*y + M[0,2]
        lat = M[1,0]*x + M[1,1]*y + M[1,2]

    Row 2 is always ``[0, 0, 1]`` to preserve the homogeneous form.
    The inverse (``geographic_to_source``) applies ``M^-1 @ [lon, lat, 1]^T``.

    A model can be set two ways:
    - **Explicit matrix**: ``update_model(transform_matrix=M)``
    - **From GCPs**: ``solve_from_gcps(gcps)`` fits M via least squares.
    """

    def __init__(self):
        super().__init__()
        self._transform_matrix: np.ndarray | None = None
        self._inverse_matrix: np.ndarray | None = None

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform a source image pixel to geographic coordinates.

        Applies ``M @ [x, y, 1]^T`` and maps result[0] → longitude,
        result[1] → latitude.

        Args:
            pixel: Source image pixel coordinates.

        Returns:
            Geographic coordinates (lat, lon).

        Raises:
            ValueError: If ``update_model`` has not been called.
        """
        if self._transform_matrix is None:
            raise ValueError("Transform matrix not set. Call update_model() first.")

        # Apply affine transformation: [x', y', 1] = M * [x, y, 1]
        p = np.array([pixel.x_px, pixel.y_px, 1.0])
        result = self._transform_matrix @ p
        return Geographic(latitude_deg=result[1], longitude_deg=result[0])

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to source image pixel.

        Applies ``M^-1 @ [lon, lat, 1]^T`` and maps result[0] → x,
        result[1] → y.

        Args:
            geo: Geographic coordinates.

        Returns:
            Source image pixel coordinates.

        Raises:
            ValueError: If ``update_model`` has not been called.
        """
        if self._inverse_matrix is None:
            raise ValueError("Inverse matrix not set. Call update_model() first.")

        # Apply inverse transformation: [x, y, 1] = M_inv * [x', y', 1]
        g = np.array([geo.longitude_deg, geo.latitude_deg, 1.0])
        result = self._inverse_matrix @ g
        return Pixel(x_px=result[0], y_px=result[1])


    def update_model(self, **kwargs) -> None:
        """Set the affine transformation matrix.

        Keyword Args:
            transform_matrix: 3x3 list or ndarray where row 0 is the
                longitude equation and row 1 is the latitude equation.
                Row 2 must be ``[0, 0, 1]``.
            image_bounds (optional): ``(min_x, min_y, max_x, max_y)`` tuple
                stored for ``image_bounds()`` queries.

        Raises:
            ValueError: If ``transform_matrix`` is missing or singular.
        """
        if 'transform_matrix' not in kwargs:
            raise ValueError("transform_matrix required for affine projector")

        matrix_list = kwargs['transform_matrix']
        self._transform_matrix = np.array(matrix_list, dtype=float)
        try:
            self._inverse_matrix = np.linalg.inv(self._transform_matrix)
        except np.linalg.LinAlgError as e:
            raise ValueError(f"Singular matrix - cannot compute inverse: {e}") from e

        # Store image bounds if provided
        if 'image_bounds' in kwargs:
            self.set_source_image_attributes(bounds=kwargs['image_bounds'])

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.AFFINE

    @property
    def is_identity(self) -> bool:
        return False

    def serialize_model_data(self) -> dict:
        """Serialize the affine transformation matrices to a dict.

        Returns:
            Dict with 'transform_matrix' and 'inverse_matrix' as lists.
        """
        if self._transform_matrix is None:
            raise ValueError("Transform matrix not set. Cannot serialize.")

        return {
            'transform_matrix': self._transform_matrix.tolist(),
            'inverse_matrix': self._inverse_matrix.tolist() if self._inverse_matrix is not None else None
        }

    def deserialize_model_data(self, data: dict) -> None:
        """Deserialize affine transformation matrices from a dict.

        Args:
            data: Dict with 'transform_matrix' and optionally 'inverse_matrix',
                  or old format with nested 'affine_data' structure.
        """
        # Handle old sidecar format with nested affine_data
        if 'affine_data' in data:
            data = data['affine_data']

        if 'transform_matrix' not in data:
            raise ValueError("transform_matrix required for deserialization")

        transform_matrix = np.array(data['transform_matrix'], dtype=float)
        self._transform_matrix = transform_matrix

        if 'inverse_matrix' in data and data['inverse_matrix'] is not None:
            self._inverse_matrix = np.array(data['inverse_matrix'], dtype=float)
        else:
            try:
                self._inverse_matrix = np.linalg.inv(transform_matrix)
            except np.linalg.LinAlgError:
                self._inverse_matrix = None

    def solve_from_gcps(self, gcps: list[tuple[Pixel, Geographic]]) -> None:
        """Fit affine transformation matrix from Ground Control Points.

        Solves two independent linear systems via least squares::

            lon = a*x + b*y + c
            lat = d*x + e*y + f

        The resulting 3x3 matrix is ``[[a,b,c], [d,e,f], [0,0,1]]``.

        Args:
            gcps: List of (Pixel, Geographic) pairs.
                  Requires at least 3 non-collinear points.

        Raises:
            ValueError: If fewer than 3 GCPs or points are collinear.
        """
        if len(gcps) < 3:
            raise ValueError(f"At least 3 GCPs required for affine solve, got {len(gcps)}")

        pixels = [p for p, _ in gcps]
        geos = [g for _, g in gcps]

        A = np.array([[p.x_px, p.y_px, 1.0] for p in pixels])
        lons = np.array([g.longitude_deg for g in geos])
        lats = np.array([g.latitude_deg for g in geos])

        row_lon, _, rank_lon, _ = np.linalg.lstsq(A, lons, rcond=None)
        row_lat, _, rank_lat, _ = np.linalg.lstsq(A, lats, rcond=None)

        if rank_lon < 3 or rank_lat < 3:
            raise ValueError("GCPs are collinear or degenerate - cannot solve affine transform")

        self.update_model(transform_matrix=np.array([
            row_lon.tolist(),
            row_lat.tolist(),
            [0.0, 0.0, 1.0],
        ]))

    def image_bounds(self) -> list[Pixel]:
        """Return image bounding box as 4 corner pixels.

        Uses bounds stored in source_image_attributes (set via update_model).
        """
        attrs = self.source_image_attributes
        if 'bounds' not in attrs:
            raise ValueError("Image bounds not set. Pass 'image_bounds' to update_model().")

        bounds = attrs['bounds']  # (min_x, min_y, max_x, max_y)
        return [
            Pixel(x_px=bounds[0], y_px=bounds[1]),  # Top-left
            Pixel(x_px=bounds[2], y_px=bounds[1]),  # Top-right
            Pixel(x_px=bounds[2], y_px=bounds[3]),  # Bottom-right
            Pixel(x_px=bounds[0], y_px=bounds[3]),  # Bottom-left
        ]

    def geographic_bounds(self) -> list[Geographic]:
        """Return geographic bounding polygon vertices.

        Transforms image_bounds corners to geographic coordinates.
        """
        image_corners = self.image_bounds()
        return [self.source_to_geographic(pixel) for pixel in image_corners]
