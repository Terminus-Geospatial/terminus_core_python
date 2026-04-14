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
#    File:    factory.py
#    Author:  Marvin Smith
#    Date:    04/10/2026
#
"""
Projector factory for creating projector instances from transformation types.
"""

# Project Libraries
from tmns.geo.proj.affine import Affine
from tmns.geo.proj.base import Transformation_Type
from tmns.geo.proj.identity import Identity
from tmns.geo.proj.rpc import RPC
from tmns.geo.proj.tps import TPS


def create_projector(transformation_type: Transformation_Type):
    """Factory function to create a projector instance.

    Args:
        transformation_type: The type of projector to create.

    Returns:
        Projector instance of the appropriate type.

    Raises:
        ValueError: If the transformation type is unknown.
    """
    if transformation_type == Transformation_Type.IDENTITY:
        return Identity()
    elif transformation_type == Transformation_Type.AFFINE:
        return Affine()
    elif transformation_type == Transformation_Type.TPS:
        return TPS()
    elif transformation_type == Transformation_Type.RPC:
        return RPC()
    else:
        raise ValueError(f"Unknown transformation type: {transformation_type}")
