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

# Base classes and enums
from tmns.geo.proj.base import Projector, Transformation_Type

# Projector implementations
from tmns.geo.proj.identity import Identity
from tmns.geo.proj.affine import Affine
from tmns.geo.proj.rpc import RPC
from tmns.geo.proj.tps import TPS

# Ground Control Points
from tmns.geo.proj.gcp import GCP

__all__ = [
    # Base classes
    'Projector',
    'Transformation_Type',
    
    # Projector implementations
    'Identity',
    'Affine', 
    'RPC',
    'TPS',
    
    # Ground Control Points
    'GCP',
]
