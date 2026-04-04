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
#    File:    __init__.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Coordinate module for terminus-core-python.

This module provides coordinate types and transformations for various
coordinate systems used in geospatial applications.
"""

# Python Standard Libraries
from __future__ import annotations
from typing import Union

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type
from tmns.geo.coord.epsg import EPSG_Manager
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.utm import UTM
from tmns.geo.coord.ups import UPS
from tmns.geo.coord.web_mercator import Web_Mercator
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.pixel import Pixel
from tmns.geo.coord.transformer import Transformer

# Union type for any coordinate type
Coordinate = Union[Geographic, UTM, UPS, Web_Mercator, ECEF, Pixel]

# Export all coordinate components
__all__ = [
    # Union type
    'Coordinate',

    # Coordinate types
    'Coordinate_Type',
    'Geographic',
    'UTM',
    'UPS',
    'Web_Mercator',
    'ECEF',
    'Pixel',

    # Utilities
    'EPSG_Manager',
    'Transformer',
]
