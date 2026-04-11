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
#    File:    constants.py
#    Author:  Marvin Smith
#    Date:    04/10/2026
#
"""
Geographic constants for the WGS-84 ellipsoid and related computations.
"""

# Python Standard Libraries
import math

# Project Libraries
from tmns.geo.hdatum import WGS84

_WGS84 = WGS84()

EARTH_CIRCUMFERENCE_M: float = 2.0 * math.pi * _WGS84.semi_major_axis
"""Equatorial circumference of the Earth in metres, derived from the WGS-84 semi-major axis."""

METERS_PER_DEG_LAT: float = EARTH_CIRCUMFERENCE_M / 360.0
"""Equatorial metres per degree of latitude (WGS-84).

This is an equatorial approximation (~111,320 m/°).  For longitude scaling at a
given latitude, multiply by cos(latitude_radians):
    meters_per_deg_lon = METERS_PER_DEG_LAT * cos(lat_rad)
"""
