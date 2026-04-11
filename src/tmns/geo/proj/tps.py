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
TPS (Thin Plate Spline) projector implementation.

Overview
--------
Thin Plate Spline (TPS) is a non-parametric, scattered-data interpolation method
that produces a smooth surface minimising the bending energy (second-order Sobolev
semi-norm) subject to passing exactly through every control point.  In remote
sensing it is used to warp imagery between two coordinate systems when the
distortion cannot be modelled well by lower-order polynomials (e.g. sensor
roll/pitch jitter, terrain relief without a DEM, historic map digitisation).

Mathematical Formulation
------------------------
Given N control points {(xᵢ, yᵢ)} with target values {zᵢ}, the TPS interpolant is::

    f(x, y) = a₁ + a₂·x + a₃·y  +  Σᵢ wᵢ · φ(‖(x,y) − (xᵢ,yᵢ)‖²)

where the kernel is the *natural* thin-plate spline kernel in ℝ²::

    φ(r²) = r² · log(r²)        (with φ(0) = 0 by continuity)

This kernel minimises the bending energy integral::

    J[f] = ∬ (f_xx² + 2·f_xy² + f_yy²) dx dy

The coefficients (w, a) are found by solving the (N+3)×(N+3) saddle-point system::

    ┌ K   P ┐ ┌ w ┐   ┌ z ┐
    │       │ │   │ = │   │
    └ Pᵀ  0 ┘ └ a ┘   └ 0 ┘

where:

- **K** (NxN): K[i,j] = φ(‖(xᵢ,yᵢ) − (xⱼ,yⱼ)‖²)
- **P** (Nx3): P[i,:] = [1, xᵢ, yᵢ]  (polynomial / affine block)
- **w** (Nx1): radial basis weights
- **a** (3x1): affine coefficients [a₁, a₂, a₃]
- **z** (Nx1): target coordinate values at the control points
- Bottom block **0** enforces the orthogonality constraints
  Σwᵢ = 0, Σwᵢxᵢ = 0, Σwᵢyᵢ = 0 needed for a unique minimum-bending solution

The system is solved independently for longitude (x-target) and latitude (y-target).

Inverse Transformation
----------------------
The inverse f⁻¹ (geographic → pixel) has no closed form.  This implementation uses
Newton iteration with a numerically-computed Jacobian (forward finite differences),
starting from the nearest control point.  Convergence is typically reached in
3–10 iterations to sub-pixel accuracy for well-conditioned problems.

References
----------
- Bookstein, F. L. (1989). "Principal warps: Thin-plate splines and the
  decomposition of deformations." *IEEE Transactions on Pattern Analysis
  and Machine Intelligence*, 11(6), 567–585.
  https://doi.org/10.1109/34.24792
  (Canonical reference for TPS in computer vision / image warping.)

- Duchon, J. (1977). "Splines minimizing rotation-invariant semi-norms in
  Sobolev spaces." In W. Schempp & K. Zeller (Eds.), *Constructive Theory
  of Functions of Several Variables*, Lecture Notes in Mathematics 571,
  pp. 85-100. Springer.
  (Mathematical foundation: existence, uniqueness, and the φ = r² log r kernel.)

- Wahba, G. (1990). *Spline Models for Observational Data*. SIAM.
  (Chapter 2 covers the thin-plate spline energy minimisation framework.)

- GDAL ``gdal_tps.cpp`` — Frank Warmerdam / Even Rouault, based on
  VizGeorefSpline2D by Gilad Ronnen (VIZRT Inc.), supported by Centro di
  Ecologia Alpina.
  https://github.com/osgeo/gdal/blob/master/alg/gdal_tps.cpp
  (Production C++ reference implementation used in GDAL/OGR reprojection.)
"""

# Python Standard Libraries
import math

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class TPS(Projector):
    """Thin Plate Spline projector for non-linear pixel ↔ geographic transforms.

    Fits a TPS model from a set of Ground Control Points (GCPs) and provides
    exact forward interpolation (pixel → geographic) at all control points,
    plus iterative Newton inversion (geographic → pixel).

    The TPS is particularly suitable for:

    - **Sensor distortion correction**: roll/pitch jitter in pushbroom sensors
      that cannot be captured by a global polynomial.
    - **Historical map georeferencing**: irregular paper deformation and
      projection discontinuities.
    - **Residual correction**: refining an RPC or affine model by absorbing
      systematic local errors with a TPS overlay.

    Fitting (``update_model``) solves the (N+3)×(N+3) saddle-point linear system
    described in the module docstring.  The solution cost scales as O(N³), so
    for large GCP sets (> a few hundred points) consider a sparse/approximate
    variant (e.g. the GDAL implementation uses LAPACK via Armadillo for speed).

    See module docstring and ``update_model`` for the full mathematical detail.

    Properties
    ----------
    - Forward transformation (``source_to_geographic``) is **exact** at control
      points and smooth between them.
    - Inverse transformation (``geographic_to_source``) uses Newton iteration
      with a numerical Jacobian; converges to sub-pixel accuracy in 3–10
      iterations for well-conditioned GCP sets.
    - Requires at least **3 non-collinear** control points.
    - GCPs should be distributed across the image; clustering degrades
      the condition number of K.

    Attributes
    ----------
    _control_points : List of (Pixel, Geographic)
        GCPs used to fit the model.
    _weights_x : np.ndarray, shape (N,)
        Radial basis weights wᵢ for the longitude component.
    _weights_y : np.ndarray, shape (N,)
        Radial basis weights wᵢ for the latitude component.
    _linear_terms_x : tuple (a₁, a₂, a₃)
        Affine coefficients for longitude: lon ≈ a₁ + a₂·x + a₃·y at large scales.
    _linear_terms_y : tuple (a₁, a₂, a₃)
        Affine coefficients for latitude:  lat ≈ a₁ + a₂·x + a₃·y at large scales.
    """

    def __init__(self):
        super().__init__()
        self._control_points: list[tuple[Pixel, Geographic]] = []
        self._weights_x: np.ndarray | None = None
        self._weights_y: np.ndarray | None = None
        self._linear_terms_x: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._linear_terms_y: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform source image pixel to geographic coordinates via TPS.

        Evaluates the interpolant::

            lon(x,y) = a₁ + a₂·x + a₃·y + Σᵢ wᵢ · φ(‖(x,y)-(xᵢ,yᵢ)‖²)
            lat(x,y) = b₁ + b₂·x + b₃·y + Σᵢ vᵢ · φ(‖(x,y)-(xᵢ,yᵢ)‖²)

        where φ(r²) = r² log(r²) is the 2-D thin-plate kernel (Duchon 1977).
        The result is **exact** at all control points.

        Args:
            pixel: Source image pixel coordinates (x_px, y_px).

        Returns:
            Geographic coordinates (latitude_deg, longitude_deg).

        Raises:
            ValueError: If ``update_model`` has not been called.
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
        """Transform geographic coordinates to source image pixel via Newton iteration.

        The TPS inverse has no closed form, so this method solves the non-linear
        system f(x,y) = (lon_target, lat_target) iteratively::

            xₖ₊₁ = xₖ + J⁻¹(xₖ) · [lon_target − f_lon(xₖ),
                                      lat_target − f_lat(xₖ)]ᵀ

        where J is the 2×2 Jacobian of the forward TPS (∂lon/∂x, ∂lon/∂y,
        ∂lat/∂x, ∂lat/∂y) approximated by forward finite differences with
        step ε = 0.5 px.

        Initial guess: pixel coordinates of the nearest GCP in geographic space.

        Convergence criterion: |Δlat| < 1e-7° and |Δlon| < 1e-7° (≈ 0.01 m).
        Typically converges in 3–10 iterations for well-conditioned models.
        Iteration stops early if the Jacobian becomes singular (det < 1e-15).

        Args:
            geo: Target geographic coordinates.

        Returns:
            Source image pixel coordinates recovered by Newton iteration.

        Raises:
            ValueError: If ``update_model`` has not been called.
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

    def source_to_geographic_batch(self, pixels: np.ndarray) -> np.ndarray:
        """Transform multiple source pixels to geographic coordinates in batch.

        Vectorized version of source_to_geographic for efficient batch processing.
        Uses numpy broadcasting to compute radial basis functions for all pixels
        and control points simultaneously.

        Args:
            pixels: Array of pixel coordinates with shape (N, 2) where columns are [x_px, y_px]

        Returns:
            Array of geographic coordinates with shape (N, 2) where columns are [lon, lat]

        Raises:
            ValueError: If model not fitted or no control points.
        """
        if self._weights_x is None or self._weights_y is None:
            raise ValueError("TPS model not fitted. Call update_model() with control points first.")

        n = len(self._control_points)
        if n == 0:
            raise ValueError("No control points available for transformation.")

        # Extract control point pixel coordinates as arrays
        cp_pixels = np.array([[cp.x_px, cp.y_px] for cp, _ in self._control_points])  # (n, 2)

        # Compute radial basis functions for all pixels and control points
        # pixels: (N, 2), cp_pixels: (n, 2) -> broadcast to (N, n, 2)
        # Compute squared distances: (N, n)
        dx = pixels[:, np.newaxis, 0] - cp_pixels[np.newaxis, :, 0]  # (N, n)
        dy = pixels[:, np.newaxis, 1] - cp_pixels[np.newaxis, :, 1]  # (N, n)
        r_squared = dx * dx + dy * dy  # (N, n)

        # Compute r² log(r²) for all distances
        r_values = np.zeros_like(r_squared)
        mask = r_squared > 1e-10
        r_values[mask] = r_squared[mask] * np.log(r_squared[mask])

        # Compute transformed coordinates using matrix multiplication
        # r_values: (N, n), weights: (n,) -> dot product over n
        r_weighted_x = np.dot(r_values, self._weights_x[:n])  # (N,)
        r_weighted_y = np.dot(r_values, self._weights_y[:n])  # (N,)

        # Add linear terms
        lon = (r_weighted_x +
               self._linear_terms_x[0] +
               self._linear_terms_x[1] * pixels[:, 0] +
               self._linear_terms_x[2] * pixels[:, 1])

        lat = (r_weighted_y +
               self._linear_terms_y[0] +
               self._linear_terms_y[1] * pixels[:, 0] +
               self._linear_terms_y[2] * pixels[:, 1])

        # Stack as (N, 2) array: [lon, lat]
        return np.column_stack([lon, lat])


    def update_model(self, **kwargs) -> None:
        """Fit the TPS model to a set of Ground Control Points.

        Assembles and solves the (N+3)×(N+3) saddle-point system (see module
        docstring).  The matrix has the block structure::

            K  = φ(‖pᵢ − pⱼ‖²)  for i,j ∈ [0,N)   (radial basis block)
            P  = [1, xᵢ, yᵢ]     for i ∈ [0,N)      (polynomial block)

            ┌ K   P ┐ ┌ w ┐   ┌ z ┐
            │       │ │   │ = │   │
            └ Pᵀ  0 ┘ └ a ┘   └ 0 ┘

        Solved twice (once for longitude targets, once for latitude targets)
        using ``numpy.linalg.solve``.  Cost scales as O(N³); for N > ~200
        consider switching to a sparse or LAPACK-backed solver (cf. the GDAL
        implementation which uses Armadillo when available).

        Keyword Args:
            control_points: ``List[Tuple[Pixel, Geographic]]`` — at least 3
                non-collinear GCPs.

        Raises:
            ValueError: If ``control_points`` is missing, has fewer than 3
                entries, or if the linear system is singular (collinear points).

        References:
            Bookstein (1989), Section III; GDAL gdal_tps.cpp ``GDALCreateTPSTransformer``.
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

        except np.linalg.LinAlgError as e:
            raise ValueError("Failed to solve TPS system - control points may be collinear") from e

    def _compute_radial_basis(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Evaluate the 2-D thin-plate spline kernel φ(r²) = r² · log(r²).

        This is the unique radially-symmetric function in ℝ² that minimises
        the Sobolev bending-energy semi-norm (Duchon 1977).  The limit
        φ(0) = 0 is enforced explicitly (L'Hôpital: r² log r² → 0 as r→0).

        Args:
            x1, y1: Coordinates of the evaluation point.
            x2, y2: Coordinates of the control point.

        Returns:
            φ(r²) = r² · log(r²), or 0.0 if r² < 1e-10.
        """
        dx = x1 - x2
        dy = y1 - y2
        r_squared = dx * dx + dy * dy

        if r_squared < 1e-10:
            return 0.0
        else:
            return r_squared * math.log(r_squared)

    def solve_from_gcps(self, gcps: list[tuple[Pixel, Geographic]]) -> None:
        """Fit TPS model from Ground Control Points.

        Convenience wrapper around ``update_model(control_points=gcps)``
        so all projectors share a uniform fitting API.

        Args:
            gcps: List of (Pixel, Geographic) pairs. Requires at least 3.
        """
        self.update_model(control_points=gcps)

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.TPS

    @property
    def is_identity(self) -> bool:
        return False

    def serialize_model_data(self) -> dict:
        """Serialize the TPS model data to a dict.

        Returns:
            Dict containing control points, weights, and linear terms.
        """
        if not self._control_points:
            raise ValueError("TPS model not fitted. Cannot serialize.")

        # Convert control points to a serializable format
        serializable_control_points = [
            (
                {'x_px': p.x_px, 'y_px': p.y_px},
                {'latitude_deg': g.latitude_deg, 'longitude_deg': g.longitude_deg}
            )
            for p, g in self._control_points
        ]

        return {
            'control_points': serializable_control_points,
            'weights_x': self._weights_x.tolist() if self._weights_x is not None else None,
            'weights_y': self._weights_y.tolist() if self._weights_y is not None else None,
            'linear_terms_x': self._linear_terms_x,
            'linear_terms_y': self._linear_terms_y,
        }

    def deserialize_model_data(self, data: dict) -> None:
        """Deserialize TPS model data from a dict.

        Args:
            data: Dict containing control points, weights, and linear terms.
        """
        from tmns.geo.coord import Geographic, Pixel

        if 'control_points' not in data:
            raise ValueError("control_points required for TPS deserialization")

        # Reconstruct control points
        self._control_points = [
            (
                Pixel(x_px=cp_data[0]['x_px'], y_px=cp_data[0]['y_px']),
                Geographic(latitude_deg=cp_data[1]['latitude_deg'], longitude_deg=cp_data[1]['longitude_deg'])
            )
            for cp_data in data['control_points']
        ]

        self._weights_x = np.array(data['weights_x']) if data['weights_x'] is not None else None
        self._weights_y = np.array(data['weights_y']) if data['weights_y'] is not None else None
        self._linear_terms_x = tuple(data['linear_terms_x'])
        self._linear_terms_y = tuple(data['linear_terms_y'])

    def image_bounds(self) -> list[Pixel]:
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

    def geographic_bounds(self) -> list[Geographic]:
        """Return geographic bounding polygon vertices.

        Transforms image_bounds corners to geographic coordinates.
        """
        image_corners = self.image_bounds()
        return [self.source_to_geographic(pixel) for pixel in image_corners]
