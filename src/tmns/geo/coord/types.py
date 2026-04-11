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
#    File:    coordinate_types.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Coordinate type definitions.
"""

# Python Standard Libraries
from enum import Enum
from typing import NamedTuple


class Type(Enum):
    """Supported coordinate types."""
    GEOGRAPHIC = "geographic"
    UTM = "utm"
    UPS = "ups"
    WEB_MERCATOR = "web_mercator"
    ECEF = "ecef"
    PIXEL = "pixel"


class Extent_Params(NamedTuple):
    """Parameters for grid generation from coordinate extent.

    Attributes:
        width: Width in coordinate units (degrees for Geographic, meters for UTM)
        height: Height in coordinate units (degrees for Geographic, meters for UTM)
        step_x: Step size in x direction (lon_step for Geographic, easting_step for UTM)
        step_y: Step size in y direction (lat_step for Geographic, northing_step for UTM)
    """
    width: float
    height: float
    step_x: float
    step_y: float


__all__ = [
    'Type',
    'Extent_Params',
]
