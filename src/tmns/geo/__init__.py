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
#    Date:    4/4/2026
#
"""
Geospatial coordinate systems and transformations.

This package provides coordinate types, transformations, and utilities
for various geospatial coordinate systems used in Terminus applications.
"""

# Python Standard Libraries
import logging

# Configure logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Export coordinate components
from tmns.geo.coord import (
    Coordinate,
    Coordinate_Type,
    Geographic,
    UTM,
    UPS,
    Web_Mercator,
    ECEF,
    Pixel,
    EPSG_Manager,
    Transformer,
)

# Export datum components
from tmns.geo.datum import Datum, Vertical_Datum

# Export projector components
from tmns.geo.projector import Projector, Identity_Projection, Affine_Projection, Transformation_Type

# Export terrain components
from tmns.geo.terrain import (
    Elevation_Point,
    Elevation_Source,
    Interpolation_Method,
    Manager as Terrain_Manager,
    elevation,
    elevation_point,
)

# Export all components
__all__ = [
    # Coordinate types
    'Coordinate',
    'Coordinate_Type',
    'Geographic',
    'UTM',
    'UPS',
    'Web_Mercator',
    'ECEF',
    'Pixel',

    # Coordinate utilities
    'EPSG_Manager',
    'Transformer',

    # Datum types
    'Datum',
    'Vertical_Datum',

    # Projector types
    'Projector',
    'Identity_Projection',
    'Affine_Projection',
    'Transformation_Type',

    # Terrain types
    'Elevation_Point',
    'Elevation_Source',
    'Interpolation_Method',
    'Terrain_Manager',
    'elevation',
    'elevation_point',
]
