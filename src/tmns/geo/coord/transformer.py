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
#    File:    transformer.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Coordinate transformation utilities.
"""

# Python Standard Libraries
from typing import Union

# Third-Party Libraries
import pyproj
from pyproj import CRS

# Project Libraries
from tmns.geo.coord.types import Coordinate_Type
from tmns.geo.coord.epsg import EPSG_Manager
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.utm import UTM
from tmns.geo.coord.ups import UPS
from tmns.geo.coord.web_mercator import Web_Mercator
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.pixel import Pixel

# Union type for any coordinate type
Coordinate = Union[Geographic, UTM, UPS, Web_Mercator, ECEF, Pixel]


class Transformer:
    """Handles coordinate transformations between different coordinate systems."""

    def __init__(self):
        """Initialize transformer with common transformations."""
        self._transformers: dict[tuple[str, str], pyproj.Transformer] = {}

    def _get_transformer(self, from_crs: str, to_crs: str) -> pyproj.Transformer:
        """Get or create a transformer for the given CRS pair."""
        key = (from_crs, to_crs)

        if key not in self._transformers:
            try:
                self._transformers[key] = pyproj.Transformer.from_crs(
                    CRS(from_crs), CRS(to_crs), always_xy=True
                )
            except Exception as e:
                raise ValueError(f"Cannot create transformer from {from_crs} to {to_crs}: {e}")

        return self._transformers[key]

    # Explicit converters (type-safe)
    def geo_to_utm(self, geo: Geographic, zone: int | None = None) -> UTM | UPS:
        """Convert geographic to UTM or UPS coordinates."""
        if zone is not None:
            target_crs = f"EPSG:{32600 + zone}" if geo.latitude_deg >= 0 else f"EPSG:{32700 + zone}"
        else:
            target_crs = self.get_utm_zone(geo.longitude_deg, geo.latitude_deg)

        return self.geographic_to_projected(geo, target_crs)

    def geo_to_web_mercator(self, geo: Geographic) -> Web_Mercator:
        """Convert geographic to Web Mercator coordinates."""
        return self.geographic_to_projected(geo, "EPSG:3857")

    def geo_to_ecef(self, geo: Geographic) -> ECEF:
        """Convert geographic to ECEF coordinates."""
        transformer = self._get_transformer("EPSG:4326", "EPSG:4978")  # WGS84 to ECEF

        if geo.altitude_m is not None:
            x, y, z = transformer.transform(
                geo.longitude_deg, geo.latitude_deg, geo.altitude_m
            )
        else:
            x, y, z = transformer.transform(
                geo.longitude_deg, geo.latitude_deg, 0.0
            )

        return ECEF.create(x, y, z)

    def geo_to_ups(self, geo: Geographic) -> UPS:
        """Convert geographic to UPS coordinates."""
        if not self.is_polar_region(geo.latitude_deg):
            raise ValueError(f"Latitude {geo.latitude_deg} is not in polar region for UPS")

        target_crs = self.get_utm_zone(geo.longitude_deg, geo.latitude_deg)  # This returns UPS CRS for polar regions
        return self.geographic_to_projected(geo, target_crs)

    def ups_to_geo(self, ups: UPS) -> Geographic:
        """Convert UPS to geographic coordinates."""
        return self.projected_to_geographic(ups)

    def utm_to_geo(self, utm: UTM) -> Geographic:
        """Convert UTM to geographic coordinates."""
        return self.projected_to_geographic(utm)

    def web_mercator_to_geo(self, wm: Web_Mercator) -> Geographic:
        """Convert Web Mercator to geographic coordinates."""
        return self.projected_to_geographic(wm)

    def ecef_to_geo(self, ecef: ECEF) -> Geographic:
        """Convert ECEF to geographic coordinates."""
        transformer = self._get_transformer("EPSG:4978", "EPSG:4326")  # ECEF to WGS84

        lon, lat, alt = transformer.transform(ecef.x_m, ecef.y_m, ecef.z_m)
        return Geographic.create(lat, lon, alt)

    # Generic converter (flexible)
    def convert(self, coord: Coordinate, dest_type: Coordinate_Type) -> Coordinate:
        """Convert any coordinate to any other coordinate type."""
        # Source type detection
        source_type = coord.type()

        # Early return if same type
        if source_type == dest_type:
            return coord

        # Geographic as source
        if source_type == Coordinate_Type.GEOGRAPHIC:
            geo = coord  # type: ignore
            if dest_type == Coordinate_Type.UTM:
                return self.geo_to_utm(geo)
            elif dest_type == Coordinate_Type.UPS:
                return self.geo_to_ups(geo)
            elif dest_type == Coordinate_Type.WEB_MERCATOR:
                return self.geo_to_web_mercator(geo)
            elif dest_type == Coordinate_Type.ECEF:
                return self.geo_to_ecef(geo)
            elif dest_type == Coordinate_Type.PIXEL:
                raise ValueError("Cannot convert directly from Geographic to Pixel")

        # UTM as source
        elif source_type == Coordinate_Type.UTM:
            utm = coord  # type: ignore
            if dest_type == Coordinate_Type.GEOGRAPHIC:
                return self.utm_to_geo(utm)
            elif dest_type == Coordinate_Type.UPS:
                geo = self.utm_to_geo(utm)
                return self.geo_to_ups(geo)
            elif dest_type == Coordinate_Type.WEB_MERCATOR:
                geo = self.utm_to_geo(utm)
                return self.geo_to_web_mercator(geo)
            elif dest_type == Coordinate_Type.ECEF:
                geo = self.utm_to_geo(utm)
                return self.geo_to_ecef(geo)
            elif dest_type == Coordinate_Type.PIXEL:
                raise ValueError("Cannot convert directly from UTM to Pixel")

        # UPS as source
        elif source_type == Coordinate_Type.UPS:
            ups = coord  # type: ignore
            if dest_type == Coordinate_Type.GEOGRAPHIC:
                return self.ups_to_geo(ups)
            elif dest_type == Coordinate_Type.UTM:
                geo = self.ups_to_geo(ups)
                return self.geo_to_utm(geo)
            elif dest_type == Coordinate_Type.WEB_MERCATOR:
                geo = self.ups_to_geo(ups)
                return self.geo_to_web_mercator(geo)
            elif dest_type == Coordinate_Type.ECEF:
                geo = self.ups_to_geo(ups)
                return self.geo_to_ecef(geo)
            elif dest_type == Coordinate_Type.PIXEL:
                raise ValueError("Cannot convert directly from UPS to Pixel")

        # Web Mercator as source
        elif source_type == Coordinate_Type.WEB_MERCATOR:
            wm = coord  # type: ignore
            if dest_type == Coordinate_Type.GEOGRAPHIC:
                return self.web_mercator_to_geo(wm)
            elif dest_type == Coordinate_Type.UTM:
                geo = self.web_mercator_to_geo(wm)
                return self.geo_to_utm(geo)
            elif dest_type == Coordinate_Type.UPS:
                geo = self.web_mercator_to_geo(wm)
                return self.geo_to_ups(geo)
            elif dest_type == Coordinate_Type.ECEF:
                geo = self.web_mercator_to_geo(wm)
                return self.geo_to_ecef(geo)
            elif dest_type == Coordinate_Type.PIXEL:
                raise ValueError("Cannot convert directly from Web Mercator to Pixel")

        # ECEF as source
        elif source_type == Coordinate_Type.ECEF:
            ecef = coord  # type: ignore
            if dest_type == Coordinate_Type.GEOGRAPHIC:
                return self.ecef_to_geo(ecef)
            elif dest_type == Coordinate_Type.UTM:
                geo = self.ecef_to_geo(ecef)
                return self.geo_to_utm(geo)
            elif dest_type == Coordinate_Type.UPS:
                geo = self.ecef_to_geo(ecef)
                return self.geo_to_ups(geo)
            elif dest_type == Coordinate_Type.WEB_MERCATOR:
                geo = self.ecef_to_geo(ecef)
                return self.geo_to_web_mercator(geo)
            elif dest_type == Coordinate_Type.PIXEL:
                raise ValueError("Cannot convert directly from ECEF to Pixel")

        # Pixel as source
        elif source_type == Coordinate_Type.PIXEL:
            raise ValueError("Cannot convert from Pixel coordinates to other types")

        raise ValueError(f"Unsupported conversion from {source_type} to {dest_type}")

    def geographic_to_projected(
        self,
        geo: Geographic,
        target_crs: str = "EPSG:3857"  # Web Mercator default
    ) -> UTM | UPS | Web_Mercator:
        """Convert geographic to projected coordinates."""
        transformer = self._get_transformer(
            "EPSG:4326", target_crs  # WGS84 to target CRS
        )

        if geo.altitude_m is not None:
            easting, northing, elevation = transformer.transform(
                geo.longitude_deg, geo.latitude_deg, geo.altitude_m
            )
        else:
            easting, northing = transformer.transform(
                geo.longitude_deg, geo.latitude_deg
            )
            elevation = None

        # Return appropriate type based on target CRS
        epsg_code = EPSG_Manager.to_epsg_code(target_crs)

        if epsg_code == EPSG_Manager.WEB_MERCATOR:
            return Web_Mercator.create(easting, northing, elevation)
        elif EPSG_Manager.is_ups_zone(epsg_code):  # UPS North/South
            hemisphere = EPSG_Manager.get_ups_hemisphere(epsg_code)
            return UPS.create(easting, northing, hemisphere, elevation)
        else:
            return UTM.create(easting, northing, target_crs, elevation)

    def projected_to_geographic(
        self,
        proj: UTM | UPS | Web_Mercator,
    ) -> Geographic:
        """Convert projected to geographic coordinates."""
        transformer = self._get_transformer(
            proj.crs, "EPSG:4326"  # Projected CRS to WGS84
        )

        if proj.altitude_m is not None:
            lon, lat, elevation = transformer.transform(
                proj.easting_m, proj.northing_m, proj.altitude_m
            )
        else:
            lon, lat = transformer.transform(proj.easting_m, proj.northing_m)
            elevation = None

        return Geographic.create(lat, lon, elevation)

    def get_utm_zone(self, longitude: float, latitude: float) -> str:
        """Get UTM zone for the given geographic coordinates."""
        # Handle polar regions (UTM doesn't work well at poles)
        if latitude >= 84.0:  # North pole region
            return EPSG_Manager.to_epsg_string(EPSG_Manager.UPS_NORTH)
        elif latitude <= -80.0:  # South pole region
            return EPSG_Manager.to_epsg_string(EPSG_Manager.UPS_SOUTH)

        # Calculate UTM zone (1-60)
        zone = int((longitude + 180) / 6) + 1
        if zone > 60:
            zone = 60
        elif zone < 1:
            zone = 1

        # Determine hemisphere and create EPSG code
        hemisphere = "N" if latitude >= 0 else "S"
        epsg_code = EPSG_Manager.create_utm_epsg(zone, hemisphere)

        return EPSG_Manager.to_epsg_string(epsg_code)

    def is_polar_region(self, latitude: float) -> bool:
        """Check if latitude is in polar region where UPS should be used."""
        return latitude >= 84.0 or latitude <= -80.0

    def get_epsg_info(self, epsg_code: int) -> dict:
        """Get comprehensive information about an EPSG code."""
        return {
            'code': epsg_code,
            'string': EPSG_Manager.to_epsg_string(epsg_code),
            'coordinate_type': EPSG_Manager.get_coordinate_type(epsg_code),
            'description': EPSG_Manager.get_description(epsg_code),
            'is_utm': EPSG_Manager.is_utm_zone(epsg_code),
            'is_ups': EPSG_Manager.is_ups_zone(epsg_code),
            'is_polar': EPSG_Manager.is_polar_region(epsg_code),
        }

    def get_epsg_info_from_string(self, epsg_str: str) -> dict:
        """Get comprehensive information about an EPSG code from string."""
        epsg_code = EPSG_Manager.to_epsg_code(epsg_str)
        return self.get_epsg_info(epsg_code)

    def to_utm(self, geo: Geographic) -> UTM:
        """Convert geographic coordinates to UTM."""
        utm_crs = self.get_utm_zone(geo.longitude_deg, geo.latitude_deg)
        return self.geographic_to_projected(geo, utm_crs)


__all__ = [
    'Transformer',
    'Coordinate',
]
