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

# Python Standard Libraries

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


    def update_model(self, **kwargs) -> None:
        """Identity model doesn't need updates."""
        pass

    @property
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.IDENTITY

    def image_bounds(self) -> list[Pixel]:
        """Identity has no intrinsic image dimensions.

        Set bounds via set_source_image_attributes(bounds=(min_x, min_y, max_x, max_y)).
        """
        attrs = self.source_image_attributes
        if 'bounds' not in attrs:
            raise ValueError("Image bounds not set. Call set_source_image_attributes(bounds=...) first.")

        bounds = attrs['bounds']  # (min_x, min_y, max_x, max_y)
        return [
            Pixel(x_px=bounds[0], y_px=bounds[1]),  # Top-left
            Pixel(x_px=bounds[2], y_px=bounds[1]),  # Top-right
            Pixel(x_px=bounds[2], y_px=bounds[3]),  # Bottom-right
            Pixel(x_px=bounds[0], y_px=bounds[3]),  # Bottom-left
        ]

    def geographic_bounds(self) -> list[Geographic]:
        """Return geographic bounding polygon vertices.

        Transforms image_bounds corners to geographic coordinates.
        """
        image_corners = self.image_bounds()
        return [self.source_to_geographic(pixel) for pixel in image_corners]

    @property
    def is_identity(self) -> bool:
        return True
