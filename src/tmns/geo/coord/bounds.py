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
#    File:    bounds.py
#    Author:  Marvin Smith
#    Date:    04/10/2026
#
"""
Geographic axis-aligned bounding box.

Stored as SW (min) and NE (max) Geographic corners in WGS84 (EPSG:4326).

For projected tiles (e.g. UTM), the AABB is a conservative overestimate of the
true coverage area.  Use this only as a pre-filter; defer exact containment to
the underlying data source, which will correctly reject false positives.
"""

from __future__ import annotations

from dataclasses import dataclass

from tmns.geo.coord.geographic import Geographic


@dataclass
class Geographic_Bounds:
    """Axis-aligned bounding box in WGS84 geographic space.

    Attributes:
        min_corner: South-west corner (minimum latitude and longitude).
        max_corner: North-east corner (maximum latitude and longitude).

    Note:
        For tiles originally in a projected CRS (e.g. UTM), the reprojected
        AABB may be slightly larger than the true coverage area.  This is
        intentional — it ensures no valid tile is skipped.  Exact containment
        must be confirmed by the underlying data source.
    """

    min_corner: Geographic
    max_corner: Geographic

    def contains(self, coord: Geographic) -> bool:
        """Return True if coord falls within (or on the boundary of) this bounding box."""
        return (self.min_corner.latitude_deg <= coord.latitude_deg <= self.max_corner.latitude_deg and
                self.min_corner.longitude_deg <= coord.longitude_deg <= self.max_corner.longitude_deg)

    @staticmethod
    def from_degrees(
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
    ) -> Geographic_Bounds:
        """Build a bounding box from raw degree values."""
        return Geographic_Bounds(
            min_corner=Geographic(latitude_deg=lat_min, longitude_deg=lon_min),
            max_corner=Geographic(latitude_deg=lat_max, longitude_deg=lon_max),
        )

    def __str__(self) -> str:
        return (f"Geographic_Bounds("
                f"sw={self.min_corner}, "
                f"ne={self.max_corner})")
