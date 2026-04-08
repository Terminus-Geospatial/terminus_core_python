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
Terrain elevation module.

This module provides elevation data access from local GeoTIFF files and AWS Terrain Tiles.
It supports a catalog-based approach for managing multiple elevation data sources with caching
and vertical datum conversions.
"""

# Python Standard Libraries
import logging
import tempfile
from pathlib import Path
from typing import Any

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord import Coordinate, Geographic, Type
from tmns.geo.coord.vdatum import Base as VBase, EGM96_DATUM, NAVD88_DATUM, ELIPSOIDAL_DATUM
from tmns.geo.terrain.source import Base, GeoTIFF, Flat
from tmns.geo.terrain.elevation_point import Elevation_Point
from tmns.geo.terrain.interpolation import Interpolation_Method
from tmns.geo.terrain.catalog import Catalog
from tmns.geo.terrain.manager import Manager


def elevation(coord: Coordinate, vertical_datum: VBase | None = None) -> float | None:
    """
    Convenience function to get elevation value.

    Args:
        coord: Coordinate to query elevation for
        vertical_datum: Target vertical datum for output. If None, uses ellipsoidal heights.

    Returns:
        Elevation value in target vertical datum or None if not found
    """
    manager = Manager.global_instance()
    return manager.elevation(coord, vertical_datum)


def elevation_point(coord: Coordinate, vertical_datum: VBase | None = None) -> Elevation_Point | None:
    """
    Convenience function to get elevation point with full metadata.

    Args:
        coord: Coordinate to query elevation for
        vertical_datum: Target vertical datum for output. If None, uses ellipsoidal heights.

    Returns:
        Elevation point with metadata in target vertical datum or None if not found
    """
    manager = Manager.global_instance()
    return manager.elevation_point(coord, vertical_datum)


__all__ = [
    # Source types
    'Base',
    'GeoTIFF',
    'Flat',

    # Terrain types
    'Elevation_Point',
    'Catalog',
    'Manager',
    'Interpolation_Method',

    # Convenience functions
    'elevation',
    'elevation_point',

    # Vertical datum support
    'VBase',
    'EGM96_DATUM',
    'NAVD88_DATUM',
    'ELIPSOIDAL_DATUM',
]
