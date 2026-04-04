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
#    File:    ecef.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
ECEF (Earth-Centered, Earth-Fixed) coordinate implementation.
"""

# Python Standard Libraries
from dataclasses import dataclass
from typing import Union

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type
from tmns.geo.coord.epsg import EPSG_Manager


@dataclass
class ECEF:
    """ECEF (Earth-Centered, Earth-Fixed) coordinate (X, Y, Z)."""
    xyz: np.ndarray  # Shape (3,) for [X, Y, Z] in meters

    def __post_init__(self):
        """Validate the numpy array."""
        if not isinstance(self.xyz, np.ndarray):
            self.xyz = np.array(self.xyz, dtype=float)

        if self.xyz.shape != (3,):
            raise ValueError(f"ECEF coordinates must have shape (3,), got {self.xyz.shape}")

    @staticmethod
    def create(x_m: float, y_m: float, z_m: float) -> 'ECEF':
        """Create an ECEF coordinate from individual components."""
        return ECEF(xyz=np.array([x_m, y_m, z_m], dtype=float))

    @staticmethod
    def from_array(xyz: np.ndarray | list[float]) -> 'ECEF':
        """Create an ECEF coordinate from array or list."""
        return ECEF(xyz=np.array(xyz, dtype=float))

    def type(self) -> Coordinate_Type:
        """Get the coordinate type."""
        return Coordinate_Type.ECEF

    @property
    def x_m(self) -> float:
        """Get X coordinate in meters."""
        return float(self.xyz[0])

    @property
    def y_m(self) -> float:
        """Get Y coordinate in meters."""
        return float(self.xyz[1])

    @property
    def z_m(self) -> float:
        """Get Z coordinate in meters."""
        return float(self.xyz[2])

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert to (X, Y, Z) tuple."""
        return (float(self.xyz[0]), float(self.xyz[1]), float(self.xyz[2]))

    def to_array(self) -> np.ndarray:
        """Get coordinate as numpy array."""
        return self.xyz.copy()

    def __str__(self) -> str:
        """String representation."""
        return f"({self.x_m:.2f}, {self.y_m:.2f}, {self.z_m:.2f})"

    def to_epsg(self) -> int:
        """Get EPSG code for this coordinate."""
        return EPSG_Manager.ECEF

    @staticmethod
    def distance(coord1: ECEF, coord2: ECEF) -> float:
        """Calculate Euclidean distance between two ECEF coordinates.

        Calculates the straight-line Euclidean distance between two points
        in the Earth-Centered Earth-Fixed coordinate system.

        Args:
            coord1: First ECEF coordinate
            coord2: Second ECEF coordinate

        Returns:
            Distance in meters between the two coordinates.
        """
        # Calculate difference vector
        diff = coord2.xyz - coord1.xyz

        # Euclidean distance
        distance = np.linalg.norm(diff)
        return distance

    @staticmethod
    def bearing(from_coord: ECEF, to_coord: ECEF, as_deg: bool = True) -> float:
        """Calculate bearing from one ECEF coordinate to another.

        Note: Bearing calculation in ECEF space is not straightforward since
        ECEF coordinates are in 3D Cartesian space. This method converts
        to geographic coordinates first, then calculates bearing.

        Args:
            from_coord: Starting ECEF coordinate
            to_coord: Ending ECEF coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, π/2 = east, π = south, 3π/2 = west)
            Range is always [0, 360] degrees or [0, 2π] radians regardless of coordinate positions.
        """
        # Convert ECEF to geographic coordinates first
        from .transformer import Transformer
        transformer = Transformer()
        from_geo = transformer.ecef_to_geo(from_coord)
        to_geo = transformer.ecef_to_geo(to_coord)

        # Use geographic bearing calculation
        from .geographic import Geographic
        return Geographic.bearing(from_geo, to_geo, as_deg)

    @property
    def magnitude(self) -> float:
        """Get magnitude of the position vector."""
        return float(np.linalg.norm(self.xyz))


__all__ = [
    'ECEF',
]
