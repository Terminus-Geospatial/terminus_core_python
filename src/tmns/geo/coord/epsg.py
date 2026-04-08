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
#    File:    epsg.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
EPSG coordinate reference system management.

Provides utilities for managing EPSG codes, converting between string and integer
formats, and identifying coordinate system types including vertical datums.
"""

# Python Standard Libraries
from __future__ import annotations
from enum import IntEnum
from typing import Union

# Project Libraries
from tmns.geo.coord.types import Type


class Code(IntEnum):
    """
    EPSG coordinate reference system codes.

    Provides type-safe EPSG codes organized by coordinate system type.
    Each enum member has the integer EPSG code as its value.
    Supports dynamic UTM zone creation via factory methods.
    """

    # ===== Horizontal Coordinate Systems =====

    # Geographic coordinate systems
    WGS84 = 4326  # World Geodetic System 1984

    # Projected coordinate systems
    WEB_MERCATOR = 3857  # Web Mercator
    ECEF = 4978  # Earth-Centered, Earth-Fixed

    # Universal Polar Stereographic
    UPS_NORTH = 32661  # UPS North (Arctic)
    UPS_SOUTH = 32761  # UPS South (Antarctic)

    # UTM zone base codes (zones calculated as base + zone number)
    UTM_NORTH_BASE = 32600  # UTM Northern hemisphere base
    UTM_SOUTH_BASE = 32700  # UTM Southern hemisphere base

    # ===== Vertical Coordinate Systems =====

    # Vertical datums
    EGM96 = 5773  # Earth Gravitational Model 1996
    NAVD88 = 5703  # North American Vertical Datum 1988
    MSL = 5714  # Mean Sea Level

    @classmethod
    def create_utm(cls, zone_number: int, northern: bool = True) -> int:
        """Create a UTM zone EPSG code as integer."""
        if not 1 <= zone_number <= 60:
            raise ValueError(f"UTM zone number must be 1-60, got {zone_number}")

        if northern:
            return cls.UTM_NORTH_BASE + zone_number
        else:
            return cls.UTM_SOUTH_BASE + zone_number

    @classmethod
    def is_horizontal(cls, epsg_code: Union[int, 'Code']) -> bool:
        """Check if EPSG code represents a horizontal coordinate system."""
        code = int(epsg_code)
        return code in [
            cls.WGS84,
            cls.WEB_MERCATOR,
            cls.ECEF,
            cls.UPS_NORTH,
            cls.UPS_SOUTH,
        ] or cls.is_utm_zone(code)

    @classmethod
    def is_vertical(cls, epsg_code: Union[int, 'Code']) -> bool:
        """Check if EPSG code represents a vertical datum."""
        code = int(epsg_code)
        return code in [
            cls.EGM96,
            cls.NAVD88,
            cls.MSL,
        ]

    @classmethod
    def is_geographic(cls, epsg_code: Union[int, 'Code']) -> bool:
        """Check if EPSG code represents a geographic coordinate system."""
        code = int(epsg_code)
        return code == cls.WGS84

    @classmethod
    def is_projected(cls, epsg_code: Union[int, 'Code']) -> bool:
        """Check if EPSG code represents a projected coordinate system."""
        code = int(epsg_code)
        return code in [cls.WEB_MERCATOR] or cls.is_utm_zone(code)

    @classmethod
    def is_utm_zone(cls, epsg_code: Union[int, 'Code']) -> bool:
        """Check if EPSG code represents a UTM zone."""
        code = int(epsg_code)
        return (cls.UTM_NORTH_BASE + 1 <= code <= cls.UTM_NORTH_BASE + 60) or \
               (cls.UTM_SOUTH_BASE + 1 <= code <= cls.UTM_SOUTH_BASE + 60)

    @classmethod
    def get_utm_zone(cls, zone_number: int, northern: bool = True) -> int:
        """
        Get UTM zone EPSG code.

        Args:
            zone_number: UTM zone number (1-60)
            northern: True for northern hemisphere, False for southern

        Returns:
            Integer EPSG code for the UTM zone

        Raises:
            ValueError: If zone number is out of range
        """
        if not 1 <= zone_number <= 60:
            raise ValueError(f"UTM zone number must be 1-60, got {zone_number}")

        if northern:
            return cls.UTM_NORTH_BASE + zone_number
        else:
            return cls.UTM_SOUTH_BASE + zone_number

    @classmethod
    def parse_utm_zone(cls, epsg_code: Union[int, 'Code']) -> tuple[int, bool]:
        """
        Parse UTM zone from EPSG code.

        Args:
            epsg_code: EPSG code for UTM zone

        Returns:
            Tuple of (zone_number, northern_hemisphere)

        Raises:
            ValueError: If EPSG code is not a UTM zone
        """
        code = int(epsg_code)

        if cls.UTM_NORTH_BASE + 1 <= code <= cls.UTM_NORTH_BASE + 60:
            zone_number = code - cls.UTM_NORTH_BASE
            return zone_number, True
        elif cls.UTM_SOUTH_BASE + 1 <= code <= cls.UTM_SOUTH_BASE + 60:
            zone_number = code - cls.UTM_SOUTH_BASE
            return zone_number, False
        else:
            raise ValueError(f"EPSG code {code} is not a UTM zone")

    @property
    def epsg_code(self) -> int:
        """Get the integer EPSG code value."""
        return self.value

    def get_coordinate_type(self) -> str:
        """
        Get the coordinate system type for this EPSG code.

        Returns:
            String describing the coordinate system type
        """
        if self.is_vertical(self):
            return "vertical"
        elif self.is_horizontal(self):
            if self.is_utm_zone(self):
                zone_number, northern = self.parse_utm_zone(self)
                hemis = "North" if northern else "South"
                return f"UTM Zone {zone_number} ({hemis})"
            elif self == self.WGS84:
                return "Geographic (WGS84)"
            elif self == self.WEB_MERCATOR:
                return "Projected (Web Mercator)"
            elif self == self.ECEF:
                return "Earth-Centered Earth-Fixed"
            elif self == self.UPS_NORTH:
                return "UPS North"
            elif self == self.UPS_SOUTH:
                return "UPS South"
            else:
                return "Horizontal"
        else:
            return "Unknown"

    def to_epsg_string(self) -> str:
        """Convert to EPSG string format (e.g., 'EPSG:4326')."""
        return f"EPSG:{self.value}"

    @classmethod
    def from_epsg_string(cls, epsg_str: str) -> 'Code':
        """
        Parse EPSG string format (e.g., 'EPSG:4326') to enum.

        Args:
            epsg_str: EPSG string in format 'EPSG:XXXX'

        Returns:
            Code enum member

        Raises:
            ValueError: If string format is invalid or code not found
        """
        if not epsg_str.startswith('EPSG:'):
            raise ValueError(f"Invalid EPSG format: {epsg_str}. Expected 'EPSG:XXXX'")

        try:
            code = int(epsg_str[5:])
            return cls(code)
        except ValueError as e:
            raise ValueError(f"Invalid EPSG code number: {epsg_str}") from e

    @classmethod
    def from_string(cls, epsg_str: str) -> 'Code':
        """
        Alias for from_epsg_string for backward compatibility.

        Args:
            epsg_str: EPSG string in format 'EPSG:XXXX'

        Returns:
            Code enum member
        """
        return cls.from_epsg_string(epsg_str)


# Convenience constants for backward compatibility
WGS84_EPSG = Code.WGS84
WEB_MERCATOR_EPSG = Code.WEB_MERCATOR
ECEF_EPSG = Code.ECEF
EGM96_EPSG = Code.EGM96
NAVD88_EPSG = Code.NAVD88
MSL_EPSG = Code.MSL


class Manager:
    """Centralized EPSG code management and utilities."""

    _instance = None

    @classmethod
    def global_instance(cls) -> 'Manager':
        """Get the singleton instance of the Manager."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @staticmethod
    def to_epsg_code(epsg_str: str) -> Code:
        """Convert EPSG string (e.g., 'EPSG:4326') to Code enum."""
        return Code.from_epsg_string(epsg_str)

    @staticmethod
    def to_epsg_string(epsg_code: Union[int, Code]) -> str:
        """Convert EPSG code to string format (e.g., 'EPSG:4326')."""
        if isinstance(epsg_code, Code):
            return epsg_code.to_epsg_string()
        else:
            return f"EPSG:{epsg_code}"

    @staticmethod
    def is_utm_zone(epsg_code: Union[int, Code]) -> bool:
        """Check if EPSG code represents a UTM zone."""
        return Code.is_utm_zone(epsg_code)

    @staticmethod
    def is_ups_zone(epsg_code: Union[int, Code]) -> bool:
        """Check if EPSG code represents a UPS zone."""
        code = int(epsg_code)
        return code in [Code.UPS_NORTH, Code.UPS_SOUTH]

    @staticmethod
    def is_geographic(epsg_code: Union[int, Code]) -> bool:
        """Check if EPSG code represents a geographic coordinate system."""
        code = int(epsg_code)
        return code == Code.WGS84

    @staticmethod
    def is_projected(epsg_code: Union[int, Code]) -> bool:
        """Check if EPSG code represents a projected coordinate system."""
        code = int(epsg_code)
        return code in [Code.WEB_MERCATOR] or Code.is_utm_zone(code)

    @staticmethod
    def is_vertical_datum(epsg_code: Union[int, Code]) -> bool:
        """Check if EPSG code represents a vertical datum."""
        return Code.is_vertical(epsg_code)

    @staticmethod
    def get_utm_zone(epsg_code: Union[int, Code]) -> tuple[int, bool]:
        """Get UTM zone number and hemisphere from EPSG code."""
        return Code.parse_utm_zone(epsg_code)

    @staticmethod
    def get_coordinate_type(epsg_code: Union[int, Code]) -> Type:
        """Get coordinate type from EPSG code."""
        if Code.is_vertical(epsg_code):
            return Type.VERTICAL
        elif Code.is_geographic(epsg_code):
            return Type.GEOGRAPHIC
        elif Code.is_utm_zone(epsg_code):
            return Type.UTM
        elif Code.is_ups_zone(epsg_code):
            return Type.UPS
        elif int(epsg_code) == Code.WEB_MERCATOR:
            return Type.WEB_MERCATOR
        elif int(epsg_code) == Code.ECEF:
            return Type.ECEF
        else:
            return Type.UNKNOWN

    @staticmethod
    def create_ups_epsg(hemisphere: str) -> Code:
        """Create UPS EPSG code from hemisphere."""
        hemisphere = hemisphere.upper()
        if hemisphere == "N":
            return Code.UPS_NORTH
        elif hemisphere == "S":
            return Code.UPS_SOUTH
        else:
            raise ValueError(f"Invalid hemisphere: {hemisphere}. Must be 'N' or 'S'.")

    @staticmethod
    def get_vertical_datum(epsg_code: Union[int, Code]):
        """Get vertical datum instance from EPSG code.

        Args:
            epsg_code: EPSG code for vertical datum

        Returns:
            Vertical datum instance

        Raises:
            ValueError: If EPSG code is not recognized
            NotImplementedError: If vertical datum is not yet implemented
        """
        from tmns.geo.coord.vdatum import EGM96, NAVD88, Ellipsoidal_Datum

        code = int(epsg_code)
        if code == Code.EGM96:
            return EGM96()
        elif code == Code.NAVD88:
            return NAVD88()
        elif code == Code.MSL:
            # TODO: Implement MSL
            raise NotImplementedError(f"MSL vertical datum not yet implemented")
        else:
            raise ValueError(f"Unknown vertical datum EPSG code: {epsg_code}")
