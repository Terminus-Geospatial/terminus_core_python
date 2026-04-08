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
#    Date:    4/4/2026
#
"""
ECEF (Earth-Centered, Earth-Fixed) coordinate implementation.

The Earth-Centered Earth-Fixed (ECEF) coordinate system is a Cartesian
coordinate system with origin at the Earth's center of mass. The X-axis
points to the intersection of the equator and prime meridian (0° latitude,
0° longitude), the Y-axis points to the intersection of the equator and
90°E longitude, and the Z-axis points to the North pole.

Coordinate System:
- X-axis: 0° latitude, 0° longitude (equator, prime meridian)
- Y-axis: 0° latitude, 90°E longitude (equator, 90° east)
- Z-axis: 90° latitude (North pole)
- Units: meters

Example:
    # Create an ECEF coordinate
    ecef = ECEF.create(-2700000, -4300000, 3850000)

    # Calculate distance between ECEF coordinates
    distance = ECEF.distance(ecef1, ecef2)

    # Get position magnitude
    magnitude = ecef.magnitude
"""

# Python Standard Libraries
from dataclasses import dataclass
from typing import Union

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord.types import Type
from tmns.geo.coord.epsg import Manager
from tmns.geo.coord.crs import CRS


@dataclass
class ECEF:
    """ECEF (Earth-Centered, Earth-Fixed) coordinate for 3D Cartesian positioning.

    ECEF coordinates represent positions in a 3D Cartesian coordinate system
    centered at Earth's center of mass. This is the standard coordinate system
    used for satellite positioning and many geodetic calculations.

    Attributes:
        xyz: 3D numpy array representing [X, Y, Z] coordinates in meters
        crs: Coordinate reference system (defaults to ECEF: EPSG:4978)

    Note:
        - X-axis: Points to 0° latitude, 0° longitude
        - Y-axis: Points to 0° latitude, 90°E longitude
        - Z-axis: Points to 90° latitude (North pole)
        - Earth radius at equator: ~6,378,137 meters
        - Earth radius at poles: ~6,356,752 meters
    """
    xyz: np.ndarray  # Shape (3,) for [X, Y, Z] in meters
    crs: CRS = None  # Coordinate reference system

    def __post_init__(self):
        """Validate the numpy array and set default CRS."""
        if not isinstance(self.xyz, np.ndarray):
            self.xyz = np.array(self.xyz, dtype=float)

        if self.xyz.shape != (3,):
            raise ValueError(f"ECEF coordinates must have shape (3,), got {self.xyz.shape}")

        # Validate coordinate bounds (reasonable Earth coordinate range)
        self._validate_bounds()

        # Set default CRS if not provided
        if self.crs is None:
            self.crs = CRS.ecef()

    def _validate_bounds(self) -> None:
        """
        Validate ECEF coordinate bounds.

        ECEF coordinates should be within reasonable Earth bounds.
        Maximum distance from Earth center is approximately 42,164 km
        (geostationary orbit radius).

        Raises:
            ValueError: If coordinates are outside reasonable bounds
        """
        max_distance = 50000000.0  # 50,000 km (generous upper bound)
        distance = np.linalg.norm(self.xyz)

        if distance > max_distance:
            raise ValueError(f"ECEF coordinate distance from origin ({distance:.0f}m) exceeds maximum ({max_distance:.0f}m)")

    @staticmethod
    def create(x_m: float, y_m: float, z_m: float) -> ECEF:
        """Create an ECEF coordinate from individual components.

        Args:
            x_m: X coordinate in meters
            y_m: Y coordinate in meters
            z_m: Z coordinate in meters

        Returns:
            ECEF coordinate with specified components

        Example:
            # Create ECEF coordinate for New York City area
            ecef = ECEF.create(-2700000, -4300000, 3850000)
        """
        return ECEF(xyz=np.array([x_m, y_m, z_m], dtype=float))

    @staticmethod
    def from_array(xyz: np.ndarray | list[float]) -> ECEF:
        """Create an ECEF coordinate from array or list.

        Args:
            xyz: Array or list containing [X, Y, Z] coordinates in meters

        Returns:
            ECEF coordinate with specified components

        Raises:
            ValueError: If array does not contain exactly 3 elements

        Example:
            # Create from numpy array
            coords = np.array([-2700000, -4300000, 3850000])
            ecef = ECEF.from_array(coords)

            # Create from list
            ecef = ECEF.from_array([-2700000, -4300000, 3850000])
        """
        xyz_array = np.array(xyz, dtype=float)
        if xyz_array.shape != (3,):
            raise ValueError(f"Array must have shape (3,), got {xyz_array.shape}")
        return ECEF(xyz=xyz_array)

    def type(self) -> Type:
        """Get the coordinate type identifier.

        Returns:
            Type.ECEF indicating this is an Earth-Centered Earth-Fixed coordinate
        """
        return Type.ECEF

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

    def copy(self) -> ECEF:
        """Create an independent copy of this ECEF coordinate.

        Returns:
            New ECEF coordinate with identical values but independent object
        """
        return ECEF(xyz=self.xyz.copy(), crs=self.crs)

    def __str__(self) -> str:
        """String representation."""
        return f"ECEF({self.x_m:.2f}, {self.y_m:.2f}, {self.z_m:.2f})"

    def __hash__(self) -> int:
        """Generate hash value for ECEF coordinate.

        Returns:
            Hash based on coordinate values and CRS
        """
        return hash((self.x_m, self.y_m, self.z_m, self.crs))

    def __eq__(self, other: object) -> bool:
        """Check equality with another ECEF coordinate.

        Args:
            other: Object to compare against

        Returns:
            True if all coordinate components match exactly, False otherwise
        """
        if not isinstance(other, ECEF):
            return False
        return (self.x_m == other.x_m and
                self.y_m == other.y_m and
                self.z_m == other.z_m and
                self.crs == other.crs)

    def __add__(self, other: ECEF) -> ECEF:
        """Add two ECEF coordinates (vector addition).

        Args:
            other: Another ECEF coordinate to add

        Returns:
            New ECEF coordinate representing the vector sum

        Raises:
            TypeError: If other is not an ECEF coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, ECEF):
            raise TypeError("Can only add ECEF to ECEF")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot add ECEF coordinates in different CRS: {self.crs} vs {other.crs}")

        return ECEF(xyz=self.xyz + other.xyz, crs=self.crs)

    def __sub__(self, other: ECEF) -> ECEF:
        """Subtract two ECEF coordinates (vector subtraction).

        Args:
            other: Another ECEF coordinate to subtract

        Returns:
            New ECEF coordinate representing the vector difference

        Raises:
            TypeError: If other is not an ECEF coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, ECEF):
            raise TypeError("Can only subtract ECEF from ECEF")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot subtract ECEF coordinates in different CRS: {self.crs} vs {other.crs}")

        return ECEF(xyz=self.xyz - other.xyz, crs=self.crs)

    @staticmethod
    def distance(coord1: ECEF, coord2: ECEF) -> float:
        """Calculate Euclidean distance between two ECEF coordinates.

        Calculates the straight-line Euclidean distance between two points
        in the Earth-Centered Earth-Fixed coordinate system.

        Args:
            coord1: First ECEF coordinate
            coord2: Second ECEF coordinate

        Returns:
            Distance in meters between the two coordinates

        Example:
            ecef1 = ECEF.create(-2700000, -4300000, 3850000)
            ecef2 = ECEF.create(-2701000, -4301000, 3851000)
            distance = ECEF.distance(ecef1, ecef2)
        """
        # Calculate difference vector
        diff = coord2.xyz - coord1.xyz

        # Euclidean distance
        distance = np.linalg.norm(diff)
        return distance

    @property
    def magnitude(self) -> float:
        """Get magnitude of the position vector.

        Returns:
            Distance from Earth's center in meters

        Example:
            ecef = ECEF.create(6378137, 0, 0)  # On Earth surface at equator
            magnitude = ecef.magnitude  # ~6,378,137 meters
        """
        return float(np.linalg.norm(self.xyz))
