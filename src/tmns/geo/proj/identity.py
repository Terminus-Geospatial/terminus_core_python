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
from typing import Self, override

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj.base import Projector, Transformation_Type


class Identity(Projector):
    """Identity transformation - no coordinate change."""

    def __init__(self):
        super().__init__()

    @override
    def pixel_to_world(self, pixel: Pixel) -> Geographic:
        """Identity: pixel coordinates are treated as world/geographic (lat/lon)."""
        return Geographic(latitude_deg=pixel.x_px, longitude_deg=pixel.y_px)

    @override
    def world_to_pixel(self, geo: Geographic) -> Pixel:
        """Identity: world/geographic coordinates are treated as pixel coordinates."""
        return Pixel(x_px=geo.latitude_deg, y_px=geo.longitude_deg)


    @override
    def update_model(self, **kwargs) -> None:
        """Identity model doesn't need updates."""
        pass

    @override
    def to_params(self) -> np.ndarray:
        """Not supported for Identity — raises NotImplementedError."""
        raise NotImplementedError("Identity does not support parameter extraction for optimization")

    @override
    def from_params(self, params: np.ndarray) -> Self:
        """Not supported for Identity — raises NotImplementedError."""
        raise NotImplementedError("Identity does not support parameter-based construction")

    @property
    @override
    def transformation_type(self) -> Transformation_Type:
        return Transformation_Type.IDENTITY

    @override
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

    @override
    def geographic_bounds(self) -> list[Geographic]:
        """Return geographic bounding polygon vertices.

        Transforms image_bounds corners to geographic coordinates.
        """
        image_corners = self.image_bounds()
        return [self.source_to_geographic(pixel) for pixel in image_corners]

    @property
    @override
    def is_identity(self) -> bool:
        return True

    @override
    def serialize_model_data(self) -> dict:
        """Serialize identity model data (empty, no model state).

        Returns:
            Empty dict since Identity has no model parameters.
        """
        return {}

    @override
    def deserialize_model_data(self, data: dict) -> None:
        """Deserialize identity model data (no-op, no model state).

        Args:
            data: Dict (ignored, Identity has no model parameters).
        """
        pass

    @override
    def compute_remap_coordinates(self, lon_mesh: np.ndarray, lat_mesh: np.ndarray,
                                   src_w: int, src_h: int) -> tuple[np.ndarray, np.ndarray]:
        """Compute remap coordinates for identity transformation.

        For identity, the output geographic coordinates map directly to source pixels
        using the image bounds stored in source_image_attributes.

        Args:
            lon_mesh: Output longitude mesh (out_h, out_w)
            lat_mesh: Output latitude mesh (out_h, out_w)
            src_w: Source image width in pixels
            src_h: Source image height in pixels

        Returns:
            Tuple of (map_x, map_y) remap coordinate arrays for cv2.remap
        """
        attrs = self.source_image_attributes
        if 'bounds' not in attrs:
            raise ValueError("Image bounds not set. Call update_model() with image_bounds.")

        bounds = attrs['bounds']  # (min_x, min_y, max_x, max_y)
        min_x, min_y, max_x, max_y = bounds
        img_w = max_x - min_x
        img_h = max_y - min_y

        # For identity, map output geographic coordinates to source pixels
        # using linear interpolation based on image bounds
        lon_range = lon_mesh.max() - lon_mesh.min()
        lat_range = lat_mesh.max() - lat_mesh.min()

        # Normalize lon/lat to [0, 1] then scale to image dimensions
        map_x = ((lon_mesh - lon_mesh.min()) / lon_range * img_w + min_x).astype(np.float32)
        map_y = ((lat_mesh.max() - lat_mesh) / lat_range * img_h + min_y).astype(np.float32)

        return map_x, map_y
