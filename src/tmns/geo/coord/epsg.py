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
#    File:    epsg_manager.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
EPSG code management and utilities.
"""

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type


class EPSG_Manager:
    """Centralized EPSG code management and utilities."""

    # EPSG code constants
    WGS84 = 4326
    WEB_MERCATOR = 3857
    ECEF = 4978

    # UPS codes
    UPS_NORTH = 32661
    UPS_SOUTH = 32761

    # UTM zone base codes
    UTM_NORTH_BASE = 32600
    UTM_SOUTH_BASE = 32700

    @staticmethod
    def to_epsg_code(epsg_str: str) -> int:
        """Convert EPSG string (e.g., 'EPSG:4326') to integer code."""
        if not epsg_str.startswith('EPSG:'):
            raise ValueError(f"Invalid EPSG format: {epsg_str}")

        try:
            return int(epsg_str.split(':')[1])
        except (IndexError, ValueError):
            raise ValueError(f"Invalid EPSG format: {epsg_str}")

    @staticmethod
    def to_epsg_string(epsg_code: int) -> str:
        """Convert integer EPSG code to string format (e.g., 4326 -> 'EPSG:4326')."""
        return f"EPSG:{epsg_code}"

    @staticmethod
    def is_utm_zone(epsg_code: int) -> bool:
        """Check if EPSG code represents a UTM zone."""
        # UTM zones are 32601-32660 (North) and 32701-32760 (South)
        return (32601 <= epsg_code <= 32660) or (32701 <= epsg_code <= 32760)

    @staticmethod
    def is_ups_zone(epsg_code: int) -> bool:
        """Check if EPSG code represents a UPS zone."""
        return epsg_code in [EPSG_Manager.UPS_NORTH, EPSG_Manager.UPS_SOUTH]

    @staticmethod
    def is_polar_region(epsg_code: int) -> bool:
        """Check if EPSG code represents a polar region (UPS)."""
        return EPSG_Manager.is_ups_zone(epsg_code)

    @staticmethod
    def get_utm_zone_number(epsg_code: int) -> int:
        """Get UTM zone number from EPSG code."""
        if not EPSG_Manager.is_utm_zone(epsg_code):
            raise ValueError(f"Not a UTM zone: {epsg_code}")

        if 32601 <= epsg_code <= 32660:
            return epsg_code - 32600
        else:  # 32701-32760
            return epsg_code - 32700

    @staticmethod
    def get_utm_hemisphere(epsg_code: int) -> str:
        """Get UTM hemisphere from EPSG code."""
        if not EPSG_Manager.is_utm_zone(epsg_code):
            raise ValueError(f"Not a UTM zone: {epsg_code}")

        return "N" if 32601 <= epsg_code <= 32660 else "S"

    @staticmethod
    def get_ups_hemisphere(epsg_code: int) -> str:
        """Get UPS hemisphere from EPSG code."""
        if not EPSG_Manager.is_ups_zone(epsg_code):
            raise ValueError(f"Not a UPS zone: {epsg_code}")

        return "N" if epsg_code == EPSG_Manager.UPS_NORTH else "S"

    @staticmethod
    def create_utm_epsg(zone: int, hemisphere: str) -> int:
        """Create UTM EPSG code from zone and hemisphere."""
        if not 1 <= zone <= 60:
            raise ValueError(f"Invalid UTM zone: {zone}. Must be 1-60.")

        hemisphere = hemisphere.upper()
        if hemisphere not in ["N", "S"]:
            raise ValueError(f"Invalid hemisphere: {hemisphere}. Must be 'N' or 'S'.")

        if hemisphere == "N":
            return EPSG_Manager.UTM_NORTH_BASE + zone
        else:
            return EPSG_Manager.UTM_SOUTH_BASE + zone

    @staticmethod
    def create_ups_epsg(hemisphere: str) -> int:
        """Create UPS EPSG code from hemisphere."""
        hemisphere = hemisphere.upper()
        if hemisphere == "N":
            return EPSG_Manager.UPS_NORTH
        elif hemisphere == "S":
            return EPSG_Manager.UPS_SOUTH
        else:
            raise ValueError(f"Invalid hemisphere: {hemisphere}. Must be 'N' or 'S'.")

    @staticmethod
    def get_coordinate_type(epsg_code: int) -> Coordinate_Type | None:
        """Get coordinate type from EPSG code."""
        if epsg_code == EPSG_Manager.WGS84:
            return Coordinate_Type.GEOGRAPHIC
        elif epsg_code == EPSG_Manager.WEB_MERCATOR:
            return Coordinate_Type.WEB_MERCATOR
        elif epsg_code == EPSG_Manager.ECEF:
            return Coordinate_Type.ECEF
        elif EPSG_Manager.is_utm_zone(epsg_code):
            return Coordinate_Type.UTM
        elif EPSG_Manager.is_ups_zone(epsg_code):
            return Coordinate_Type.UPS
        else:
            return None

    @staticmethod
    def get_description(epsg_code: int) -> str:
        """Get description of EPSG code."""
        descriptions = {
            EPSG_Manager.WGS84: "WGS84 Geographic",
            EPSG_Manager.WEB_MERCATOR: "Web Mercator",
            EPSG_Manager.ECEF: "Earth-Centered Earth-Fixed",
            EPSG_Manager.UPS_NORTH: "Universal Polar Stereographic (N)",
            EPSG_Manager.UPS_SOUTH: "Universal Polar Stereographic (S)",
        }

        if epsg_code in descriptions:
            return descriptions[epsg_code]
        elif EPSG_Manager.is_utm_zone(epsg_code):
            zone = EPSG_Manager.get_utm_zone_number(epsg_code)
            hemisphere = EPSG_Manager.get_utm_hemisphere(epsg_code)
            return f"UTM Zone {zone}{hemisphere}"
        else:
            return f"Unknown EPSG:{epsg_code}"


__all__ = [
    'EPSG_Manager',
]
