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

# Export geographic constants
from tmns.geo.constants import EARTH_CIRCUMFERENCE_M, METERS_PER_DEG_LAT

# Export coordinate components
from tmns.geo.coord import (
    ECEF,
    UPS,
    UTM,
    Coordinate,
    Geographic,
    Geographic_Bounds,
    Manager,
    Pixel,
    Transformer,
    Type,
    Web_Mercator,
)
from tmns.geo.coord.vdatum import EGM96, NAVD88, Ellipsoidal_Datum
from tmns.geo.coord.vdatum import Base as VBase
from tmns.geo.hdatum import WGS84

# Export datum components
from tmns.geo.hdatum import Base as HBase

# Export LTP components
from tmns.geo.ltp import Local_Tangent_Plane

# Export projector components
from tmns.geo.proj import (
    GCP,
    RPC,
    TPS,
    Affine,
    Identity,
    Projector,
    Transformation_Type,
)
from tmns.geo.terrain import (
    Base as Terrain_Base,
)

# Export terrain components
from tmns.geo.terrain import (
    Catalog,
    Elevation_Point,
    Flat,
    GeoTIFF,
    Interpolation_Method,
    elevation,
    elevation_point,
)
from tmns.geo.terrain import (
    Manager as Terrain_Manager,
)

# Export all components
__all__ = [
    # Geographic constants
    'EARTH_CIRCUMFERENCE_M',
    'METERS_PER_DEG_LAT',

    # Coordinate utilities
    'Coordinate',
    'Type',
    'Geographic',
    'Geographic_Bounds',
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
