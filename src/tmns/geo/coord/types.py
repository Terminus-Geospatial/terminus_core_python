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


class Coordinate_Type(Enum):
    """Supported coordinate types."""
    GEOGRAPHIC = "geographic"
    UTM = "utm"
    UPS = "ups"
    WEB_MERCATOR = "web_mercator"
    ECEF = "ecef"
    PIXEL = "pixel"


__all__ = [
    'Coordinate_Type',
]
