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
#    File:    interpolation.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Terrain elevation interpolation methods.
"""

#  Python Standard Libraries
from enum import Enum


class Interpolation_Method(Enum):
    """Elevation interpolation methods."""
    NEAREST = "nearest"
    BILINEAR = "bilinear"
    CUBIC = "cubic"
