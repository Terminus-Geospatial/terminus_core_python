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
from typing import Self, override

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

    MIN_GCPS = 3  # Minimum GCPs required for affine transform

    def __init__(self):
        super().__init__()
        self._transform_matrix: np.ndarray | None = None
        self._inverse_matrix: np.ndarray | None = None
        self._image_size: tuple[int, int] | None = None  # (width, height)

    @override
    def pixel_to_world(self, pixel: Pixel) -> Geographic:
        """Transform a source image pixel to world (geographic) coordinates.

        Applies ``M @ [x, y, 1]^T`` and maps result[0] → longitude,
        result[1] → latitude.

        Args:
            pixel: Source image pixel coordinates.

        Returns:
            World (geographic) coordinates (lat, lon).

        Raises:
            ValueError: If ``update_model`` has not been called.
        """
        if self._transform_matrix is None:
            raise ValueError("Transform matrix not set. Call update_model() first.")

        # Apply affine transformation: [x', y', 1] = M * [x, y, 1]
        p = np.array([pixel.x_px, pixel.y_px, 1.0])
        result = self._transform_matrix @ p
        return Geographic(latitude_deg=result[1], longitude_deg=result[0])

    @override
    def world_to_pixel(self, geo: Geographic) -> Pixel:
        """Transform world (geographic) coordinates to source image pixel.

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


    @override
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

        # Store image size if provided
        if 'image_size' in kwargs:
            self._image_size = tuple(kwargs['image_size'])

    @override
    def to_params(self) -> np.ndarray:
        """Extract the 6 optimizable elements of the affine matrix.

        Returns:
            1D array [m00, m01, m02, m10, m11, m12] (first two rows of the matrix).
        """
        if self._transform_matrix is None:
            raise ValueError("Transform matrix not set. Call update_model() first.")

        return np.array([
            self._transform_matrix[0, 0],  # m00 (scale_x)
            self._transform_matrix[0, 1],  # m01 (shear_xy)
            self._transform_matrix[0, 2],  # m02 (tx)
            self._transform_matrix[1, 0],  # m10 (shear_yx)
            self._transform_matrix[1, 1],  # m11 (scale_y)
            self._transform_matrix[1, 2],  # m12 (ty)
        ])

    @override
    def from_params(self, params: np.ndarray) -> Self:
        """Create a new Affine instance with modified parameters.

        Args:
            params: 1D array of 6 parameters [m00, m01, m02, m10, m11, m12]

        Returns:
            New Affine instance with the specified transform matrix
        """
        if len(params) != 6:
            raise ValueError(f"Expected 6 parameters for Affine, got {len(params)}")

        # Reconstruct 3x3 matrix from parameters
        new_matrix = np.array([
            [params[0], params[1], params[2]],  # [m00, m01, m02]
            [params[3], params[4], params[5]],  # [m10, m11, m12]
            [0.0, 0.0, 1.0]                     # Fixed bottom row
        ])

        # Create new affine model
        new_affine = Affine()
        new_affine.update_model(transform_matrix=new_matrix)

        # Copy image size and bounds if available
        new_affine._image_size = self._image_size
        if hasattr(self, '_source_image_attrs'):
            new_affine._source_image_attrs = self._source_image_attrs.copy()

        return new_affine

    @override
    def get_param_bounds(self, bounds_px: float = 50.0) -> list[tuple[float, float]]:
        """Compute differential-evolution bounds for the 6 Affine parameters.

        Projects the 4 image corners to geographic space and derives per-coefficient
        bounds scaled by bounds_px (in pixels).

        Args:
            bounds_px: Translation search radius in pixels.

        Returns:
            List of (min, max) bounds for [m00, m01, m02, m10, m11, m12].

        Raises:
            ValueError: If image_size is not set.
        """
        if self._image_size is None:
            raise ValueError("Affine model has no image_size — cannot derive param bounds.")

        params = self.to_params()
        w, h = self._image_size

        corners = [
            Pixel(x_px=0,     y_px=0),
            Pixel(x_px=w - 1, y_px=0),
            Pixel(x_px=w - 1, y_px=h - 1),
            Pixel(x_px=0,     y_px=h - 1),
        ]
        geos = [self.pixel_to_world(c) for c in corners]
        lons = [g.longitude_deg for g in geos]
        lats = [g.latitude_deg  for g in geos]

        d_lon_per_px = (max(lons) - min(lons)) / w
        d_lat_per_px = (max(lats) - min(lats)) / h

        return [
            (params[0] - d_lon_per_px * 0.2, params[0] + d_lon_per_px * 0.2),                # m00
            (params[1] - d_lon_per_px * 0.2, params[1] + d_lon_per_px * 0.2),                # m01
            (min(lons) - d_lon_per_px * bounds_px, max(lons) + d_lon_per_px * bounds_px),    # m02 (tx)
            (params[3] - d_lat_per_px * 0.2, params[3] + d_lat_per_px * 0.2),                # m10
            (params[4] - d_lat_per_px * 0.2, params[4] + d_lat_per_px * 0.2),                # m11
            (min(lats) - d_lat_per_px * bounds_px, max(lats) + d_lat_per_px * bounds_px),    # m12 (ty)
        ]

    @property
    @override
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.AFFINE

    @property
    @override
    def is_identity(self) -> bool:
        return False

    @override
    def serialize_model_data(self) -> dict:
        """Serialize the affine transformation matrices to a dict.

        Returns:
            Dict with 'transform_matrix', 'inverse_matrix', and 'image_size' as lists.
        """
        if self._transform_matrix is None:
            raise ValueError("Transform matrix not set. Cannot serialize.")

        return {
            'transform_matrix': self._transform_matrix.tolist(),
            'inverse_matrix': self._inverse_matrix.tolist() if self._inverse_matrix is not None else None,
            'image_size': list(self._image_size) if self._image_size is not None else None,
        }

    @override
    def deserialize_model_data(self, data: dict) -> None:
        """Deserialize affine transformation matrices from a dict.

        Args:
            data: Dict with 'transform_matrix' and optionally 'inverse_matrix',
                  'image_size', or old format with nested 'affine_data' structure.
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

        if 'image_size' in data and data['image_size'] is not None:
            self._image_size = tuple(data['image_size'])

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
        return [self.pixel_to_world(pixel) for pixel in image_corners]

    def compute_remap_coordinates(self, lon_mesh: np.ndarray, lat_mesh: np.ndarray,
                                   src_w: int, src_h: int) -> tuple[np.ndarray, np.ndarray]:
        """Compute remap coordinates for affine transformation.

        Args:
            lon_mesh: Output longitude mesh (out_h, out_w)
            lat_mesh: Output latitude mesh (out_h, out_w)
            src_w: Source image width in pixels
            src_h: Source image height in pixels

        Returns:
            Tuple of (map_x, map_y) remap coordinate arrays for cv2.remap
        """
        if self._inverse_matrix is None:
            raise ValueError("Inverse matrix not set. Call update_model() first.")

        out_h, out_w = lon_mesh.shape
        inv = self._inverse_matrix
        ones = np.ones_like(lon_mesh)
        geo_coords = np.stack([lon_mesh, lat_mesh, ones], axis=0)
        px = (inv @ geo_coords.reshape(3, -1)).reshape(3, out_h, out_w)
        map_x = px[0].astype(np.float32)
        map_y = px[1].astype(np.float32)
        return map_x, map_y
