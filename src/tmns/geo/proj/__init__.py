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
Projection and coordinate transformation module
"""

# Python Standard Libraries
from typing import Union

# Base classes and enums
from tmns.geo.proj.affine import Affine
from tmns.geo.proj.base import Projector, Transformation_Type, Warp_Extent

# Ground Control Points
from tmns.geo.proj.gcp import GCP

# Projector implementations
from tmns.geo.proj.identity import Identity
from tmns.geo.proj.rpc import RPC
from tmns.geo.proj.tps import TPS

# Type aliases for common projector combinations
# Use this alias instead of maintaining Affine | TPS | RPC in multiple places
Projector_Union = Union[Affine, TPS, RPC]

__all__ = [
    # Base classes
    'Projector',
    'Transformation_Type',
    'Warp_Extent',

    # Projector implementations
    'Identity',
    'Affine',
    'RPC',
    'TPS',

    # Ground Control Points
    'GCP',

    # Type aliases
    'Projector_Union',
]
