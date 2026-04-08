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
#    Date:    4/7/2026
#
"""
Elevation source module.

This module provides elevation data sources with a clean, extensible architecture.
All elevation sources inherit from a common Base class and provide consistent
interfaces for accessing elevation data.
"""

# Python Standard Libraries
from typing import Any

# Project Libraries
from tmns.geo.terrain.source.base import Base
from tmns.geo.terrain.source.flat import Flat
from tmns.geo.terrain.source.geotiff import GeoTIFF

# Export all source components
__all__ = [
    # Base class
    'Base',

    # Specific implementations
    'GeoTIFF',
    'Flat',
]
