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
#    File:    base.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Projector base classes and enums
"""

# Python Standard Libraries
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict

# Project Libraries
from tmns.geo.coord import Geographic, Pixel


class Transformation_Type(Enum):
    """Supported transformation types for coordinate projections."""
    IDENTITY = "identity"
    AFFINE = "affine"
    RPC = "rpc"
    TPS = "tps"


class Projector(ABC):
    """Abstract base class for coordinate transformation projectors."""

    def __init__(self):
        self._source_image_attrs: Dict[str, Any] = {}
        self._destination_image_attrs: Dict[str, Any] = {}

    @abstractmethod
    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform source image pixel coordinates to geographic coordinates."""
        pass

    @abstractmethod
    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to source image pixel coordinates."""
        pass

    @abstractmethod
    def destination_to_geographic(self, pixel: Pixel) -> Geographic:
        """Transform destination image pixel coordinates to geographic coordinates."""
        pass

    @abstractmethod
    def geographic_to_destination(self, geo: Geographic) -> Pixel:
        """Transform geographic coordinates to destination image pixel coordinates."""
        pass

    @abstractmethod
    def update_model(self, **kwargs) -> None:
        """Update the transformation model with new parameters."""
        pass

    @property
    @abstractmethod
    def transformation_type(self) -> Transformation_Type:
        """Return the type of transformation (e.g., IDENTITY, RPC, AFFINE, TPS)."""
        pass

    @property
    @abstractmethod
    def is_identity(self) -> bool:
        """Return True if this is an identity transformation."""
        pass

    @property
    def source_image_attributes(self) -> Dict[str, Any]:
        """Get source image attributes."""
        return self._source_image_attrs.copy()

    @property
    def destination_image_attributes(self) -> Dict[str, Any]:
        """Get destination image attributes."""
        return self._destination_image_attrs.copy()

    def set_source_image_attributes(self, **attrs) -> None:
        """Set source image attributes."""
        self._source_image_attrs.update(attrs)

    def set_destination_image_attributes(self, **attrs) -> None:
        """Set destination image attributes."""
        self._destination_image_attrs.update(attrs)
