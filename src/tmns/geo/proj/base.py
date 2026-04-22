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
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, NamedTuple, Self

# Third-Party Libraries
import numpy as np

# Project Libraries
from tmns.geo.coord import Geographic, Pixel
from tmns.geo.coord.crs import CRS
from tmns.geo.coord.transformer import Transformer


class Warp_Extent(NamedTuple):
    """Geographic bounding extent for warp operations."""
    min_point: Geographic
    max_point: Geographic
    corners: list  # [TL, TR, BR, BL] as Geographic

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary with min_point, max_point, and corners
        """
        return {
            'min_point': (self.min_point.latitude_deg, self.min_point.longitude_deg),
            'max_point': (self.max_point.latitude_deg, self.max_point.longitude_deg),
            'corners': [(c.longitude_deg, c.latitude_deg) for c in self.corners] if self.corners else None
        }

    @staticmethod
    def from_dict(data: dict) -> Warp_Extent:
        """Create Warp_Extent from dictionary.

        Args:
            data: Dictionary with min_point, max_point, and optionally corners

        Returns:
            Warp_Extent instance
        """
        # Handle corners
        corners = None
        if data.get('corners'):
            corners = [Geographic(longitude_deg=c[0], latitude_deg=c[1]) for c in data['corners']]

        min_point = Geographic(latitude_deg=data['min_point'][0],
                               longitude_deg=data['min_point'][1])
        max_point = Geographic(latitude_deg=data['max_point'][0],
                               longitude_deg=data['max_point'][1])

        return Warp_Extent(min_point=min_point, max_point=max_point, corners=corners)

    def compute_output_size(self, crs: CRS, gsd: float) -> tuple[int, int]:
        """Compute output size (width, height) from extent, CRS, and GSD.

        Args:
            crs: Output coordinate reference system
            gsd: Ground sample distance in meters (UTM) or degrees (WGS84)

        Returns:
            Tuple of (width, height) in pixels
        """
        if crs.is_utm_zone():
            # UTM: convert extent corners to UTM to get dimensions in meters
            transformer = Transformer()
            zone = crs.get_utm_zone_info()[0]
            utm_min = transformer.geo_to_utm(self.min_point, zone=zone)
            utm_max = transformer.geo_to_utm(self.max_point, zone=zone)
            width_m = utm_max.easting_m - utm_min.easting_m
            height_m = utm_max.northing_m - utm_min.northing_m
            return int(width_m / gsd), int(height_m / gsd)
        else:
            # WGS84: extent is in degrees
            width_deg = self.max_point.longitude_deg - self.min_point.longitude_deg
            height_deg = self.max_point.latitude_deg - self.min_point.latitude_deg
            return int(width_deg / gsd), int(height_deg / gsd)


class Transformation_Type(Enum):
    """Supported transformation types for coordinate projections."""
    IDENTITY = "identity"
    AFFINE = "affine"
    RPC = "rpc"
    TPS = "tps"


class Projector(ABC):
    """Abstract base class for coordinate transformation projectors."""

    def __init__(self):
        self._source_image_attrs: dict[str, Any] = {}

    @abstractmethod
    def pixel_to_world(self, pixel: Pixel) -> Geographic:
        """Transform source image pixel coordinates to world (geographic) coordinates."""
        pass

    @abstractmethod
    def world_to_pixel(self, geo: Geographic) -> Pixel:
        """Transform world (geographic) coordinates to source image pixel coordinates."""
        pass


    @abstractmethod
    def update_model(self, **kwargs) -> None:
        """Update the transformation model with new parameters."""
        pass

    @abstractmethod
    def to_params(self) -> np.ndarray:
        """Extract optimizable parameters from the model.

        Returns:
            1D array of current model parameters.
        """
        pass

    @abstractmethod
    def from_params(self, params: np.ndarray) -> Self:
        """Create a new model instance with modified parameters.

        Args:
            params: 1D array of model parameters (same structure as to_params output)

        Returns:
            New instance of the same type with the specified parameters.
        """
        pass

    @abstractmethod
    def get_param_bounds(self, bounds_px: float = 50.0) -> list[tuple[float, float]]:
        """Compute parameter bounds for optimization.

        Args:
            bounds_px: Translation search radius in pixels.

        Returns:
            List of (min, max) bounds for each parameter in to_params().
        """
        pass

    @abstractmethod
    def serialize_model_data(self) -> dict:
        """Serialize the transformation model data to a dict for persistence.

        Returns:
            Dict containing model-specific data (e.g., transform matrices, coefficients).
        """
        pass

    @abstractmethod
    def deserialize_model_data(self, data: dict) -> None:
        """Deserialize model data from a dict and apply to this projector.

        Args:
            data: Dict containing model-specific data as returned by serialize_model_data.
        """
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

    @abstractmethod
    def image_bounds(self) -> list[Pixel]:
        """Return image bounding box as 4 corner pixels.

        Returns list of Pixel in order: [top-left, top-right, bottom-right, bottom-left]
        """
        pass

    @abstractmethod
    def geographic_bounds(self) -> list[Geographic]:
        """Return geographic bounding polygon vertices.

        Transforms image_bounds corners to geographic coordinates.
        Returns list of Geographic in order: [top-left, top-right, bottom-right, bottom-left]
        """
        pass

    @abstractmethod
    def compute_remap_coordinates(self, lon_mesh: np.ndarray, lat_mesh: np.ndarray,
                                   src_w: int, src_h: int) -> tuple[np.ndarray, np.ndarray]:
        """Compute remap coordinates for warping.

        Args:
            lon_mesh: Output longitude mesh (out_h, out_w)
            lat_mesh: Output latitude mesh (out_h, out_w)
            src_w: Source image width in pixels
            src_h: Source image height in pixels

        Returns:
            Tuple of (map_x, map_y) remap coordinate arrays for cv2.remap
        """
        pass

    @property
    def source_image_attributes(self) -> dict[str, Any]:
        """Get source image attributes."""
        return self._source_image_attrs.copy()

    def set_source_image_attributes(self, **attrs) -> None:
        """Set source image attributes."""
        self._source_image_attrs.update(attrs)

    def warp_extent(self, src_w: int, src_h: int) -> Warp_Extent:
        """Return the geographic bounding extent for warping a src_w x src_h image.

        Computes geographic coordinates of the four image corners and returns
        the axis-aligned bounding box plus the corner list.

        Args:
            src_w: Source image width in pixels.
            src_h: Source image height in pixels.

        Returns:
            Warp_Extent with lon/lat min/max and the four geographic corners.
        """
        corners_px = [
            Pixel(x_px=0,       y_px=0),
            Pixel(x_px=src_w-1, y_px=0),
            Pixel(x_px=src_w-1, y_px=src_h-1),
            Pixel(x_px=0,       y_px=src_h-1),
        ]
        corners_geo = [self.pixel_to_world(p) for p in corners_px]
        lons = [g.longitude_deg for g in corners_geo]
        lats = [g.latitude_deg  for g in corners_geo]
        min_point = Geographic.create(min(lats), min(lons))
        max_point = Geographic.create(max(lats), max(lons))
        return Warp_Extent(
            min_point=min_point,
            max_point=max_point,
            corners=corners_geo,
        )
