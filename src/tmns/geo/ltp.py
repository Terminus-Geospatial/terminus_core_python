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
#    File:    ltp.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Local Tangent Plane coordinate transformations.

Provides coordinate transformations between different local coordinate systems
(ENU, NED) and global coordinate systems (ECEF, Geographic).
"""

import math

import numpy as np

from tmns.geo.coord.ecef import ECEF

# Project Libraries
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.transformer import Transformer


class Local_Tangent_Plane:
    """
    Local Tangent Plane (LTP) coordinate transformations.

    Provides static methods for coordinate transformations between:
    - ENU (East, North, Up)
    - NED (North, East, Down)
    - ECEF (Earth-Centered, Earth-Fixed)
    - Geographic (latitude, longitude, altitude)
    """

    @staticmethod
    def ecef_to_ned_matrix(reference_geo: Geographic, dims: int = 3) -> np.ndarray:
        """
        Return a rotation matrix that converts ECEF vectors to NED.

        Args:
            reference_geo: Reference geographic location for the NED frame
            dims: Dimension of the matrix (must be >= 3)

        Returns:
            ECEF to NED rotation matrix
        """
        if dims < 3:
            raise ValueError(f"dims must be >= 3, got {dims}")

        lat_rad = math.radians(reference_geo.latitude_deg)
        lon_rad = math.radians(reference_geo.longitude_deg)

        matrix = np.eye(dims, dtype=np.float64)

        # ECEF to NED rotation matrix (from reference implementation)
        matrix[0:3, 0:3] = np.array([
            [-math.sin(lat_rad) * math.cos(lon_rad), -math.sin(lat_rad) * math.sin(lon_rad), math.cos(lat_rad)],
            [-math.sin(lon_rad), math.cos(lon_rad), 0.0],
            [-math.cos(lat_rad) * math.cos(lon_rad), -math.cos(lat_rad) * math.sin(lon_rad), -math.sin(lat_rad)]
        ], dtype=np.float64)

        return matrix

    @staticmethod
    def ned_to_ecef_matrix(reference_geo: Geographic, dims: int = 3) -> np.ndarray:
        """
        Return a rotation matrix that converts NED vectors to ECEF.

        Args:
            reference_geo: Reference geographic location for the NED frame
            dims: Dimension of the matrix (must be >= 3)

        Returns:
            NED to ECEF rotation matrix (transpose of ECEF to NED)
        """
        return Local_Tangent_Plane.ecef_to_ned_matrix(reference_geo, dims).T

    @staticmethod
    def ned_to_enu_matrix(dims: int = 3) -> np.ndarray:
        """
        Return a rotation matrix that converts NED vectors to ENU.

        Args:
            dims: Dimension of the matrix (must be >= 3)

        Returns:
            NED to ENU rotation matrix
        """
        if dims < 3:
            raise ValueError(f"dims must be >= 3, got {dims}")

        matrix = np.eye(dims, dtype=np.float64)

        # NED to ENU rotation matrix (swap axes and flip up/down)
        matrix[0:3, 0:3] = np.array([
            [0.0, 1.0, 0.0],   # East = North (NED)
            [1.0, 0.0, 0.0],   # North = East (NED)
            [0.0, 0.0, -1.0]   # Up = -Down (NED)
        ], dtype=np.float64)

        return matrix

    @staticmethod
    def enu_to_ned_matrix(dims: int = 3) -> np.ndarray:
        """
        Return a rotation matrix that converts ENU vectors to NED.

        Args:
            dims: Dimension of the matrix (must be >= 3)

        Returns:
            ENU to NED rotation matrix (transpose of NED to ENU)
        """
        return Local_Tangent_Plane.ned_to_enu_matrix(dims).T

    @staticmethod
    def enu_to_ecef_matrix(reference_geo: Geographic, dims: int = 3) -> np.ndarray:
        """
        Return a rotation matrix that converts ENU vectors to ECEF.

        Args:
            reference_geo: Reference geographic location for the ENU frame
            dims: Dimension of the matrix (must be >= 3)

        Returns:
            ENU to ECEF rotation matrix (combines enu_to_ned and ned_to_ecef)
        """
        ned_to_ecef = Local_Tangent_Plane.ned_to_ecef_matrix(reference_geo, dims)
        enu_to_ned = Local_Tangent_Plane.enu_to_ned_matrix(dims)
        return ned_to_ecef @ enu_to_ned

    @staticmethod
    def ecef_to_enu_matrix(reference_geo: Geographic, dims: int = 3) -> np.ndarray:
        """
        Return a rotation matrix that converts ECEF vectors to ENU.

        Args:
            reference_geo: Reference geographic location for the ENU frame
            dims: Dimension of the matrix (must be >= 3)

        Returns:
            ECEF to ENU rotation matrix (transpose of ENU to ECEF)
        """
        return Local_Tangent_Plane.enu_to_ecef_matrix(reference_geo, dims).T

    @staticmethod
    def ecef_to_ned(ecef_point: ECEF | np.ndarray | list,
                    reference_geo: Geographic) -> np.ndarray:
        """
        Convert ECEF coordinates to NED.

        Args:
            ecef_point: ECEF coordinates
            reference_geo: Reference geographic location for the NED frame

        Returns:
            NED coordinates [north, east, down] in meters
        """
        if isinstance(ecef_point, ECEF):
            ecef_array = ecef_point.to_array()
        else:
            ecef_array = np.array(ecef_point).flatten()

        # Get reference ECEF coordinates
        transformer = Transformer()
        ref_ecef = transformer.geo_to_ecef(reference_geo)
        ref_array = ref_ecef.to_array()

        # Calculate relative position and apply rotation
        rel_ecef = ecef_array - ref_array
        matrix = Local_Tangent_Plane.ecef_to_ned_matrix(reference_geo, 3)
        ned_array = matrix @ rel_ecef

        return ned_array

    @staticmethod
    def ned_to_ecef(ned_point: np.ndarray | list,
                    reference_geo: Geographic) -> ECEF:
        """
        Convert NED coordinates to ECEF.

        Args:
            ned_point: NED coordinates [north, east, down] in meters
            reference_geo: Reference geographic location for the NED frame

        Returns:
            ECEF coordinates
        """
        ned_array = np.array(ned_point).flatten()

        # Get reference ECEF coordinates
        transformer = Transformer()
        ref_ecef = transformer.geo_to_ecef(reference_geo)
        ref_array = ref_ecef.to_array()

        # Apply rotation and translation
        matrix = Local_Tangent_Plane.ned_to_ecef_matrix(reference_geo, 3)
        ecef_offset = matrix @ ned_array
        ecef_array = ref_array + ecef_offset

        return ECEF.create(ecef_array[0], ecef_array[1], ecef_array[2])

    @staticmethod
    def enu_to_ned(enu_point: np.ndarray | list) -> np.ndarray:
        """
        Convert ENU coordinates to NED.

        Args:
            enu_point: ENU coordinates [east, north, up] in meters

        Returns:
            NED coordinates [north, east, down] in meters
        """
        enu_array = np.array(enu_point).flatten()
        matrix = Local_Tangent_Plane.enu_to_ned_matrix(3)
        ned_array = matrix @ enu_array
        return ned_array

    @staticmethod
    def ned_to_enu(ned_point: np.ndarray | list) -> np.ndarray:
        """
        Convert NED coordinates to ENU.

        Args:
            ned_point: NED coordinates [north, east, down] in meters

        Returns:
            ENU coordinates [east, north, up] in meters
        """
        ned_array = np.array(ned_point).flatten()
        matrix = Local_Tangent_Plane.ned_to_enu_matrix(3)
        enu_array = matrix @ ned_array
        return enu_array

    @staticmethod
    def ecef_to_enu(ecef_point: ECEF | np.ndarray | list,
                    reference_geo: Geographic) -> np.ndarray:
        """
        Convert ECEF coordinates to ENU.

        Args:
            ecef_point: ECEF coordinates
            reference_geo: Reference geographic location for the ENU frame

        Returns:
            ENU coordinates [east, north, up] in meters
        """
        # Convert ECEF to NED, then NED to ENU
        ned_array = Local_Tangent_Plane.ecef_to_ned(ecef_point, reference_geo)
        enu_array = Local_Tangent_Plane.ned_to_enu(ned_array)
        return enu_array

    @staticmethod
    def enu_to_ecef(enu_point: np.ndarray | list,
                    reference_geo: Geographic) -> ECEF:
        """
        Convert ENU coordinates to ECEF.

        Args:
            enu_point: ENU coordinates [east, north, up] in meters
            reference_geo: Reference geographic location for the ENU frame

        Returns:
            ECEF coordinates
        """
        # Convert ENU to NED, then NED to ECEF
        ned_array = Local_Tangent_Plane.enu_to_ned(enu_point)
        ecef_point = Local_Tangent_Plane.ned_to_ecef(ned_array, reference_geo)
        return ecef_point

    @staticmethod
    def geographic_to_enu(geo_point: Geographic, reference_geo: Geographic) -> np.ndarray:
        """
        Convert geographic coordinates to ENU.

        Args:
            geo_point: Geographic coordinates to convert
            reference_geo: Reference geographic location for the ENU frame

        Returns:
            ENU coordinates [east, north, up] in meters
        """
        transformer = Transformer()
        ecef_point = transformer.geo_to_ecef(geo_point)
        return Local_Tangent_Plane.ecef_to_enu(ecef_point, reference_geo)

    @staticmethod
    def enu_to_geographic(enu_point: np.ndarray | list,
                          reference_geo: Geographic) -> Geographic:
        """
        Convert ENU coordinates to geographic.

        Args:
            enu_point: ENU coordinates [east, north, up] in meters
            reference_geo: Reference geographic location for the ENU frame

        Returns:
            Geographic coordinates
        """
        ecef_point = Local_Tangent_Plane.enu_to_ecef(enu_point, reference_geo)
        transformer = Transformer()
        return transformer.ecef_to_geo(ecef_point)


__all__ = [
    'Local_Tangent_Plane',
]
