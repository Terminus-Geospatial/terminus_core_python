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
#    File:    identity.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Identity projector implementation
"""

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class Identity(Projector):
    """Identity transformation - no coordinate change."""

    def __init__(self):
        super().__init__()

    def source_to_geographic(self, pixel: Pixel) -> Geographic:
        """Identity: pixel coordinates are treated as geographic (lat/lon)."""
        return Geographic(latitude_deg=pixel.x_px, longitude_deg=pixel.y_px)

    def geographic_to_source(self, geo: Geographic) -> Pixel:
        """Identity: geographic coordinates are treated as pixel coordinates."""
        return Pixel(x_px=geo.latitude_deg, y_px=geo.longitude_deg)

    def destination_to_geographic(self, pixel: Pixel) -> Geographic:
        """Identity: pixel coordinates are treated as geographic (lat/lon)."""
        return Geographic(latitude_deg=pixel.x_px, longitude_deg=pixel.y_px)

    def geographic_to_destination(self, geo: Geographic) -> Pixel:
        """Identity: geographic coordinates are treated as pixel coordinates."""
        return Pixel(x_px=geo.latitude_deg, y_px=geo.longitude_deg)

    def update_model(self, **kwargs) -> None:
        """Identity model doesn't need updates."""
        pass

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.IDENTITY

    @property
    def is_identity(self) -> bool:
        return True
