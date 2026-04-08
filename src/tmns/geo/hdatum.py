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
#    File:    hdatum.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Horizontal geodetic datum definitions and utilities.

This module contains horizontal reference ellipsoid definitions used for
geodetic calculations and coordinate transformations.
"""

# Python Standard Libraries
from dataclasses import dataclass
import math
from typing import Union

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.transformer import Transformer


@dataclass
class Base:
    """
    Horizontal geodetic datum with ellipsoidal parameters.

    Represents a reference ellipsoid used for geodetic calculations. Provides
    methods for ray-ellipsoid intersection and coordinate transformations.

    Attributes:
        semi_major_axis: Equatorial radius (a) in meters
        flattening: Ellipsoid flattening (f), dimensionless
    """
    semi_major_axis: float  # a (meters)
    flattening: float       # f (dimensionless)

    @property
    def semi_minor_axis(self) -> float:
        """
        Calculate semi-minor axis (polar radius).

        Returns:
            Polar radius (b) in meters: b = a * (1 - f)
        """
        return self.semi_major_axis * (1 - self.flattening)

    def ray_ellipsoid_intersection(self, origin: Union[ECEF, Geographic, np.ndarray],
                                     direction: np.ndarray) -> Geographic:
        """
        Find intersection of ray with ellipsoid surface using analytical solution.

        Solves the quadratic equation for ray-ellipsoid intersection:
            (x/a)^2 + (y/a)^2 + (z/b)^2 = 1

        where the ray is defined as: P(t) = origin + t * direction

        Args:
            origin: Ray origin as ECEF, Geographic, or numpy array [x, y, z] in ECEF meters
            direction: Ray direction vector (vx, vy, vz) in ECEF frame, need not be normalized

        Returns:
            Intersection point as Geographic (latitude, longitude, altitude)

        Raises:
            ValueError: If ray does not intersect ellipsoid

        Example:
            >>> datum = WGS84()
            >>> origin = ECEF.create(0, 0, 7000000)  # 7000 km above pole
            >>> direction = np.array([0, 0, -1])     # Pointing down
            >>> intersection = datum.ray_ellipsoid_intersection(origin, direction)
            >>> print(f"Lat: {intersection.latitude_deg:.6f}°")
        """
        # Convert origin to ECEF if needed
        if isinstance(origin, Geographic):
            transformer = Transformer()
            origin_ecef = transformer.geo_to_ecef(origin)
        elif isinstance(origin, ECEF):
            origin_ecef = origin
        else:
            # Assume numpy array
            origin_flat = origin.flatten()
            origin_ecef = ECEF.create(origin_flat[0], origin_flat[1], origin_flat[2])

        # Extract ECEF components
        origin_array = origin_ecef.to_array()
        x0, y0, z0 = origin_array[0], origin_array[1], origin_array[2]

        # Extract direction components
        direction_flat = direction.flatten()
        vx, vy, vz = direction_flat[0], direction_flat[1], direction_flat[2]

        a = self.semi_major_axis
        b = self.semi_minor_axis

        # Quadratic coefficients for intersection: A*t^2 + B*t + C = 0
        A = (vx**2 + vy**2) / (a**2) + (vz**2) / (b**2)
        B = 2 * ((x0 * vx + y0 * vy) / (a**2) + (z0 * vz) / (b**2))
        C = (x0**2 + y0**2) / (a**2) + (z0**2) / (b**2) - 1

        # Check that A is non-zero (direction vector cannot be all zeros)
        if abs(A) < 1e-15:
            raise ValueError("Invalid direction vector: cannot be zero or near-zero magnitude.")

        # Solve quadratic equation
        discriminant = B**2 - 4 * A * C
        if discriminant < 0:
            raise ValueError("No intersection with the ellipsoid (ray misses surface).")

        sqrt_disc = math.sqrt(discriminant)

        # Two potential solutions
        t1 = (-B - sqrt_disc) / (2 * A)
        t2 = (-B + sqrt_disc) / (2 * A)

        # Choose smallest positive t (closest intersection in forward direction)
        t_candidates = [t for t in (t1, t2) if t >= 0]

        if not t_candidates:
            raise ValueError("Ray does not intersect ellipsoid in forward direction.")

        t = min(t_candidates)

        # Compute intersection point in ECEF
        xi = x0 + t * vx
        yi = y0 + t * vy
        zi = z0 + t * vz

        # Convert to Geographic
        intersection_ecef = ECEF.create(xi, yi, zi)
        transformer = Transformer()
        return transformer.ecef_to_geo(intersection_ecef)

    def check_ray_ellipsoid_intersection(self, origin: Union[ECEF, Geographic, np.ndarray],
                                          direction: np.ndarray) -> bool:
        """
        Check if ray intersects ellipsoid surface without computing the intersection.

        This is a convenience method that returns True/False instead of raising exceptions.
        Useful for validation or filtering rays before computing actual intersections.

        Args:
            origin: Ray origin as ECEF, Geographic, or numpy array [x, y, z] in ECEF meters
            direction: Ray direction vector (vx, vy, vz) in ECEF frame, need not be normalized

        Returns:
            True if ray intersects ellipsoid in forward direction, False otherwise

        Example:
            >>> datum = WGS84()
            >>> origin = ECEF.create(0, 0, 7000000)
            >>> direction = np.array([0, 0, -1])
            >>> if datum.check_ray_ellipsoid_intersection(origin, direction):
            ...     intersection = datum.ray_ellipsoid_intersection(origin, direction)
        """
        try:
            self.ray_ellipsoid_intersection(origin, direction)
            return True
        except ValueError:
            return False


class WGS84(Base):
    """
    WGS84 (World Geodetic System 1984) datum.

    The most widely used geodetic datum for GPS and global mapping.
    EPSG code: 4326 (geographic coordinates)

    Parameters:
        - Semi-major axis (a): 6,378,137.0 meters
        - Flattening (f): 1 / 298.257223563
        - Semi-minor axis (b): ~6,356,752.314 meters

    References:
        - NIMA TR8350.2, "Department of Defense World Geodetic System 1984"
        - EPSG:4326

    Example:
        >>> wgs84 = WGS84()
        >>> print(f"Equatorial radius: {wgs84.semi_major_axis:.1f} m")
        >>> print(f"Polar radius: {wgs84.semi_minor_axis:.3f} m")
    """

    def __init__(self):
        """Initialize WGS84 datum with standard parameters."""
        super().__init__(
            semi_major_axis=6378137.0,           # meters
            flattening=1.0 / 298.257223563       # dimensionless
        )