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
#    File:    web_mercator.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Web Mercator coordinate implementation.

Web Mercator (EPSG:3857) is a projected coordinate system widely used in web mapping
applications like Google Maps, OpenStreetMap, and other tile-based mapping services.
It projects the Earth onto a square grid suitable for tiled map display.

The coordinate system uses meters for easting and northing values, with the world
extending from approximately -20,037,508 to 20,037,508 meters in both directions.
"""

# Python Standard Libraries
from __future__ import annotations

import math
from collections import namedtuple
from dataclasses import dataclass

# Third-Party Libraries
import numpy as np

from tmns.geo.coord.crs import CRS

# Project Libraries
from tmns.geo.coord.types import Type

# Web Mercator bounds as namedtuple for lightweight structure
Web_Mercator_Bounds = namedtuple('Web_Mercator_Bounds', ['min_easting', 'min_northing', 'max_easting', 'max_northing'])


@dataclass
class Web_Mercator:
    """
    Web Mercator coordinate (easting, northing, elevation).

    Represents a point in the Web Mercator projected coordinate system (EPSG:3857),
    commonly used by web mapping services like Google Maps, OpenStreetMap,
    and other slippy map implementations.

    Web Mercator is a conformal projection that preserves shapes locally but
    distorts area and distance, especially at high latitudes. The projection
    treats the Earth as a sphere rather than an ellipsoid for computational
    efficiency.

    Attributes:
        easting_m: East coordinate in meters (horizontal position)
        northing_m: North coordinate in meters (vertical position)
        altitude_m: Height above/below reference surface in meters
        crs: Coordinate reference system object

    Class Attributes:
        MIN_BOUND: Minimum valid coordinate value (-20,037,508.342789244 m)
        MAX_BOUND: Maximum valid coordinate value (20,037,508.342789244 m)
        WORLD_WIDTH_M: Width of the world in Web Mercator projection
        BASE_TILE_SIZE: Default tile size in pixels (256)
    """

    # Web Mercator Constants
    MIN_BOUND = -20037508.342789244
    MAX_BOUND = 20037508.342789244
    WORLD_WIDTH_M = 40075016.68557849
    BASE_TILE_SIZE = 256

    easting_m: float
    northing_m: float
    altitude_m: float | None = None
    crs: CRS = CRS.from_epsg(3857)

    # ============================================================================
    # CORE METHODS
    # ============================================================================

    @staticmethod
    def create(easting_m: float, northing_m: float, alt_m: float | None = None) -> Web_Mercator:
        """
        Create a Web Mercator coordinate.

        Args:
            easting_m: Easting coordinate in meters
            northing_m: Northing coordinate in meters
            alt_m: Altitude in meters above sea level (optional)

        Returns:
            Web_Mercator coordinate instance
        """
        return Web_Mercator(easting_m=easting_m, northing_m=northing_m, crs="EPSG:3857", altitude_m=alt_m)

    def type(self) -> Type:
        """
        Get the coordinate type.

        Returns:
            Type.WEB_MERCATOR enum value
        """
        return Type.WEB_MERCATOR

    def to_tuple(self) -> tuple[float, float]:
        """
        Convert to (easting, northing) tuple.

        Returns:
            Tuple containing (easting_m, northing_m)
        """
        return (self.easting_m, self.northing_m)

    def to_3d_tuple(self) -> tuple[float, float, float]:
        """
        Convert to (easting, northing, elevation) tuple.

        Returns:
            Tuple containing (easting_m, northing_m, altitude_m or 0.0)
        """
        return (self.easting_m, self.northing_m, self.altitude_m or 0.0)

    def copy(self) -> Web_Mercator:
        """
        Create a copy of this Web Mercator coordinate.

        Returns:
            New Web_Mercator instance with identical values
        """
        return Web_Mercator(easting_m=self.easting_m, northing_m=self.northing_m,
                           altitude_m=self.altitude_m, crs=self.crs)

    def __hash__(self) -> int:
        """
        Make Web_Mercator hashable for use in sets and as dictionary keys.

        Returns:
            Hash value based on coordinate components
        """
        return hash((self.easting_m, self.northing_m, self.altitude_m, self.crs))

    def __eq__(self, other: object) -> bool:
        """
        Check equality with another Web Mercator coordinate.

        Args:
            other: Object to compare against

        Returns:
            True if coordinates are identical, False otherwise
        """
        if not isinstance(other, Web_Mercator):
            return False
        return (self.easting_m == other.easting_m and
                self.northing_m == other.northing_m and
                self.altitude_m == other.altitude_m and
                self.crs == other.crs)

    def __str__(self) -> str:
        """
        String representation of the coordinate.

        Returns:
            Human-readable string representation
        """
        return f"Web_Mercator(easting={self.easting_m:.2f}, northing={self.northing_m:.2f}, altitude={self.altitude_m})"

    def __add__(self, other: Web_Mercator) -> Web_Mercator:
        """
        Add two Web Mercator coordinates (vector addition).

        Performs vector addition of coordinates, requiring both coordinates
        to be in the same coordinate reference system.

        Args:
            other: Web_Mercator coordinate to add

        Returns:
            New Web_Mercator coordinate representing the sum

        Raises:
            TypeError: If other is not a Web_Mercator coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, Web_Mercator):
            raise TypeError("Can only add Web_Mercator to Web_Mercator")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot add Web_Mercator coordinates in different CRS: {self.crs} vs {other.crs}")

        return Web_Mercator(easting_m=self.easting_m + other.easting_m,
                           northing_m=self.northing_m + other.northing_m,
                           altitude_m=self.altitude_m if self.altitude_m is not None else other.altitude_m,
                           crs=self.crs)

    def __sub__(self, other: Web_Mercator) -> Web_Mercator:
        """
        Subtract two Web Mercator coordinates (vector subtraction).

        Performs vector subtraction of coordinates, requiring both coordinates
        to be in the same coordinate reference system.

        Args:
            other: Web_Mercator coordinate to subtract

        Returns:
            New Web_Mercator coordinate representing the difference

        Raises:
            TypeError: If other is not a Web_Mercator coordinate
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(other, Web_Mercator):
            raise TypeError("Can only subtract Web_Mercator from Web_Mercator")

        # Validate that both coordinates are in the same CRS
        if self.crs != other.crs:
            raise ValueError(f"Cannot subtract Web_Mercator coordinates in different CRS: {self.crs} vs {other.crs}")

        return Web_Mercator(easting_m=self.easting_m - other.easting_m,
                           northing_m=self.northing_m - other.northing_m,
                           altitude_m=self.altitude_m if self.altitude_m is not None else other.altitude_m,
                           crs=self.crs)

    def is_in_bounds(self) -> bool:
        """
        Check if coordinate is within valid Web Mercator world bounds.

        Web Mercator has a square world extent from -20037508.342789244 to
        20037508.342789244 meters in both easting and northing directions.

        Returns:
            True if coordinate is within valid world bounds, False otherwise
        """
        return (Web_Mercator.MIN_BOUND <= self.easting_m <= Web_Mercator.MAX_BOUND and
                Web_Mercator.MIN_BOUND <= self.northing_m <= Web_Mercator.MAX_BOUND)

    def meters_per_pixel(self, zoom_level: int) -> float:
        """
        Calculate meters per pixel at given zoom level.

        Web Mercator uses a consistent scale where at zoom level 0, the entire
        world (approximately 40,075,016 meters wide) fits into 256 pixels.
        Each subsequent zoom level doubles the resolution.

        Args:
            zoom_level: Web map zoom level (typically 0-20)

        Returns:
            Meters per pixel at the specified zoom level
        """
        pixels_at_zoom = Web_Mercator.BASE_TILE_SIZE * (2 ** zoom_level)
        return Web_Mercator.WORLD_WIDTH_M / pixels_at_zoom

    def tile_coordinates(self, zoom_level: int) -> tuple[int, int]:
        """
        Calculate tile coordinates at given zoom level.

        Converts Web Mercator coordinates to the tile grid system used by
        web mapping services. Tiles are typically 256x256 pixels.

        Args:
            zoom_level: Web map zoom level (typically 0-20)

        Returns:
            Tuple of (tile_x, tile_y) coordinates
        """
        scale = Web_Mercator.WORLD_WIDTH_M / (2 ** zoom_level)

        tile_x = int((self.easting_m + Web_Mercator.WORLD_WIDTH_M/2) / scale)
        tile_y = int((Web_Mercator.WORLD_WIDTH_M/2 - self.northing_m) / scale)

        return (tile_x, tile_y)

    def pixel_coordinates(self, zoom_level: int, tile_size: int = 256) -> tuple[int, int]:
        """
        Calculate pixel coordinates within tile at given zoom level.

        Determines the exact pixel location within a map tile for the
        coordinate position. Useful for rendering and interaction.

        Args:
            zoom_level: Web map zoom level (typically 0-20)
            tile_size: Size of map tiles in pixels (default: 256)

        Returns:
            Tuple of (pixel_x, pixel_y) coordinates within the tile
        """
        # Calculate world pixel coordinates first
        scale = Web_Mercator.WORLD_WIDTH_M / (2 ** zoom_level)
        world_pixel_x = (self.easting_m + Web_Mercator.WORLD_WIDTH_M/2) / scale
        world_pixel_y = (Web_Mercator.WORLD_WIDTH_M/2 - self.northing_m) / scale

        # Convert to tile-relative pixel coordinates
        tile_x = int(world_pixel_x / tile_size)
        tile_y = int(world_pixel_y / tile_size)

        pixel_x = int(world_pixel_x - tile_x * tile_size)
        pixel_y = int(world_pixel_y - tile_y * tile_size)

        # Ensure within bounds
        pixel_x = max(0, min(pixel_x, tile_size - 1))
        pixel_y = max(0, min(pixel_y, tile_size - 1))

        return (pixel_x, pixel_y)

    @staticmethod
    def world_bounds() -> Web_Mercator_Bounds:
        """
        Get Web Mercator world bounds.

        Returns the valid coordinate range for the Web Mercator projection,
        which forms a square approximately 40,075 km on each side.

        Returns:
            Web_Mercator_Bounds with min/max easting and northing values
        """
        return Web_Mercator_Bounds(
            min_easting=Web_Mercator.MIN_BOUND,
            min_northing=Web_Mercator.MIN_BOUND,
            max_easting=Web_Mercator.MAX_BOUND,
            max_northing=Web_Mercator.MAX_BOUND
        )

    @staticmethod
    def distance(coord1: Web_Mercator, coord2: Web_Mercator) -> float:
        """
        Calculate Euclidean distance between two Web Mercator coordinates.

        Computes the straight-line Euclidean distance between two points
        in the Web Mercator coordinate system. Both coordinates must be
        in the same coordinate reference system.

        Args:
            coord1: First Web Mercator coordinate
            coord2: Second Web Mercator coordinate

        Returns:
            Distance in meters between the two coordinates

        Raises:
            TypeError: If either coordinate is not a Web_Mercator
            ValueError: If coordinates are in different CRS
        """
        if not isinstance(coord1, Web_Mercator) or not isinstance(coord2, Web_Mercator):
            raise TypeError("Can only calculate distance between Web_Mercator coordinates")

        # Validate that both coordinates are in the same CRS
        if coord1.crs != coord2.crs:
            raise ValueError(f"Cannot calculate distance between Web_Mercator coordinates in different CRS: {coord1.crs} vs {coord2.crs}")

        dx = coord1.easting_m - coord2.easting_m
        dy = coord1.northing_m - coord2.northing_m
        return math.sqrt(dx*dx + dy*dy)

    @staticmethod
    def bearing(from_coord: Web_Mercator, to_coord: Web_Mercator, as_deg: bool = True) -> float:
        """
        Calculate bearing from one Web Mercator coordinate to another.

        Computes the compass bearing from a starting coordinate to an ending
        coordinate in the Web Mercator projection system. The bearing is
        measured clockwise from true north.

        Args:
            from_coord: Starting Web Mercator coordinate
            to_coord: Ending Web Mercator coordinate
            as_deg: If True, return bearing in degrees; if False, return bearing in radians

        Returns:
            Bearing measured clockwise from true north:
            - If as_deg=True: degrees (0° = north, 90° = east, 180° = south, 270° = west)
            - If as_deg=False: radians (0 = north, Ï/2 = east, Ï = south, 3Ï/2 = west)
            Range is always [0, 360] degrees or [0, 2Ï] radians regardless of coordinate positions.

        Raises:
            ValueError: If coordinates are in different coordinate systems
        """
        # Web Mercator coordinates should all use the same CRS (EPSG:3857)
        # But we validate for consistency
        if from_coord.crs != to_coord.crs:
            raise ValueError(f"Cannot calculate bearing between coordinates in different coordinate systems: {from_coord.crs} vs {to_coord.crs}")

        # Calculate bearing in Web Mercator coordinate system
        dx = to_coord.easting_m - from_coord.easting_m
        dy = to_coord.northing_m - from_coord.northing_m

        bearing = np.arctan2(dx, dy)  # Note: dx/easting, dy/northing for bearing

        # Normalize to [0, 2π] radians
        bearing = (bearing + 2 * np.pi) % (2 * np.pi)

        # Convert to degrees if requested
        if as_deg:
            bearing = np.degrees(bearing)

        return bearing
