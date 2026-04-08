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

# Export coordinate components
from tmns.geo.coord import (
    Coordinate,
    Type,
    Geographic,
    UTM,
    UPS,
    Web_Mercator,
    ECEF,
    Pixel,
    Manager,
    Transformer,
)

# Export datum components
from tmns.geo.hdatum import Base as HBase, WGS84
from tmns.geo.coord.vdatum import Base as VBase, EGM96, NAVD88, Ellipsoidal_Datum

# Export LTP components
from tmns.geo.ltp import Local_Tangent_Plane

# Export projector components
from tmns.geo.proj import Projector, Identity, Affine, RPC, TPS, GCP, Transformation_Type

# Export terrain components
from tmns.geo.terrain import (
    Elevation_Point,
    Base as Terrain_Base,
    GeoTIFF,
    Flat,
    Catalog,
    Manager as Terrain_Manager,
    Interpolation_Method,
    elevation,
    elevation_point,
)

# Export all components
__all__ = [
    # Coordinate utilities
    'Coordinate',
    'Type',
    'Geographic',
    'UTM',
    'UPS',
    'Web_Mercator',
    'ECEF',
    'Pixel',
    'Manager',
    'Transformer',

    # Datum types
    'HBase',
    'WGS84',
    'VBase',
    'EGM96',
    'NAVD88',
    'Ellipsoidal_Datum',
    'Local_Tangent_Plane',

    # Projector types
    'Projector',
    'Identity',
    'Affine',
    'RPC',
    'TPS',
    'Transformation_Type',
    'GCP',

    # Terrain types
    'Elevation_Point',
    'Terrain_Base',
    'GeoTIFF',
    'Flat',
    'Catalog',
    'Terrain_Manager',
    'Interpolation_Method',
    'elevation',
    'elevation_point',
]
