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
#    File:    gcp.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Ground Control Point (GCP) data structure.

A Ground Control Point represents a correspondence between pixel coordinates in a source
image (e.g., a satellite photo or aerial photograph) and known geographic coordinates
(e.g., latitude/longitude or projected coordinates). GCPs are fundamental to image
georeferencing and orthorectification workflows.

The GCP class stores coordinates in multiple coordinate systems to support different
transformation models and use cases:

- **test_pixel**: Pixel coordinates in the source/test image (x, y in pixels)
- **reference_pixel**: Pixel coordinates in a reference image (optional, for image-to-image registration)
- **geographic**: Geographic coordinates (latitude, longitude, elevation in degrees and meters)
- **projected**: Projected coordinates (e.g., UTM easting, northing, elevation in meters)
- **error**: Residual error from transformation fitting (optional, in pixels or meters)
- **enabled**: Flag to include/exclude GCP from computations without deleting it

Typical usage patterns:

1. **Georeferencing**: Use test_pixel and geographic to fit a transformation model
   (Affine, RPC, TPS) that maps image pixels to world coordinates.

2. **Image-to-image registration**: Use test_pixel and reference_pixel to align
   two images of the same area.

3. **Quality control**: Use error field to identify and disable poorly fitting GCPs.

4. **Serialization**: Use to_dict/from_dict for JSON persistence and interchange.

Example::

    from tmns.geo.coord import Pixel, Geographic
    from tmns.geo.proj.gcp import GCP

    # Create a GCP from image pixel to geographic coordinates
    gcp = GCP(
        id=1,
        test_pixel=Pixel(100.0, 200.0),
        reference_pixel=Pixel(150.0, 250.0),
        geographic=Geographic(35.5, -117.5, 100.0),
        error=2.5,
        enabled=True
    )

    # Serialize to dictionary for JSON storage
    gcp_dict = gcp.to_dict()

    # Deserialize from dictionary
    restored_gcp = GCP.from_dict(gcp_dict)

    # Disable a poor-quality GCP
    gcp.enabled = False

References:
- GDAL GCP documentation: https://gdal.org/tutorials/geotiff_tut.html
"""

# Python Standard Libraries
from dataclasses import dataclass, field
from typing import Any

# Project Libraries
from tmns.geo.coord import UTM, Geographic, Pixel


@dataclass
class GCP:
    """Ground Control Point with coordinates in multiple coordinate systems.

    Attributes:
        id: Unique identifier for this GCP (must be positive integer).
        test_pixel: Pixel coordinates in the source/test image (x, y in pixels).
        reference_pixel: Pixel coordinates in a reference image (x, y in pixels).
            Optional, used for image-to-image registration workflows.
        geographic: Geographic coordinates (latitude, longitude, elevation).
            Latitude and longitude in degrees, elevation in meters.
        projected: Projected coordinates (e.g., UTM easting, northing, elevation).
            Optional, used when working with projected coordinate systems.
        error: Residual error from transformation fitting. Units depend on
            transformation type (pixels for image space, meters for geographic).
            None if not yet computed.
        enabled: Whether this GCP should be included in transformation fitting.
            Allows temporary exclusion without deletion.

    Raises:
        ValueError: If id is not a positive integer.

    Example::

        gcp = GCP(
            id=1,
            test_pixel=Pixel(100.0, 200.0),
            reference_pixel=Pixel(150.0, 250.0),
            geographic=Geographic(35.5, -117.5, 100.0),
            error=2.5,
            enabled=True
        )
    """

    id: int
    test_pixel: Pixel
    reference_pixel: Pixel
    geographic: Geographic
    projected: UTM | None = None
    error: float | None = None
    enabled: bool = True
    source: str = 'manual'
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate GCP attributes after initialization.

        Raises:
            ValueError: If id is not a positive integer.
        """
        if self.id <= 0:
            raise ValueError("GCP ID must be positive")

    def to_dict(self) -> dict:
        """Convert GCP to dictionary for serialization.

        Returns:
            Dictionary representation of the GCP with nested coordinate objects.
            The dictionary structure is compatible with JSON serialization and
            the from_dict() class method for deserialization.

        Example::

            gcp = GCP(id=1, test_pixel=Pixel(100, 200), ...)
            gcp_dict = gcp.to_dict()
            # gcp_dict = {'id': 1, 'test_pixel': {'x': 100, 'y': 200}, ...}
        """
        return {
            'id': self.id,
            'test_pixel': {
                'x': self.test_pixel.x_px,
                'y': self.test_pixel.y_px
            },
            'reference_pixel': {
                'x': self.reference_pixel.x_px,
                'y': self.reference_pixel.y_px
            },
            'geographic': {
                'latitude': self.geographic.latitude_deg,
                'longitude': self.geographic.longitude_deg,
                'elevation': self.geographic.altitude_m
            },
            'projected': {
                'easting': self.projected.easting_m,
                'northing': self.projected.northing_m,
                'elevation': self.projected.altitude_m,
                'crs': self.projected.crs
            } if self.projected else None,
            'error': self.error,
            'enabled': self.enabled,
            'source': self.source,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GCP':
        """Create GCP from dictionary for deserialization.

        Args:
            data: Dictionary representation of a GCP, typically from to_dict()
                or JSON deserialization. Expected keys:
                - id (int): GCP identifier
                - test_pixel (dict): {'x': float, 'y': float} or {'x_px': float, 'y_px': float}
                - reference_pixel (dict): Same format as test_pixel
                - geographic (dict): {'latitude': float, 'longitude': float, 'elevation': float}
                    or with '_deg' and '_m' suffixes
                - projected (dict, optional): {'easting': float, 'northing': float,
                    'crs': str, 'elevation': float}
                - error (float, optional): Residual error
                - enabled (bool, optional): Whether GCP is enabled (default: True)

        Returns:
            GCP instance reconstructed from the dictionary data.

        Raises:
            KeyError: If required keys are missing from the dictionary.
            ValueError: If coordinate values are invalid.

        Example::

            gcp_dict = {
                'id': 1,
                'test_pixel': {'x': 100, 'y': 200},
                'reference_pixel': {'x': 150, 'y': 250},
                'geographic': {'latitude': 35.5, 'longitude': -117.5, 'elevation': 100.0},
                'error': 2.5,
                'enabled': True
            }
            gcp = GCP.from_dict(gcp_dict)
        """
        tp = data['test_pixel']
        test_pixel = Pixel.create(tp.get('x', tp.get('x_px')), tp.get('y', tp.get('y_px')))
        rp = data['reference_pixel']
        ref_pixel = Pixel.create(rp.get('x', rp.get('x_px')), rp.get('y', rp.get('y_px')))

        geo_data = data['geographic']
        geographic = Geographic.create(
            geo_data.get('latitude', geo_data.get('latitude_deg')),
            geo_data.get('longitude', geo_data.get('longitude_deg')),
            geo_data.get('elevation', geo_data.get('altitude_m'))
        )

        projected = None
        if data.get('projected'):
            proj_data = data['projected']
            projected = UTM.create(
                proj_data['easting'],
                proj_data['northing'],
                proj_data.get('crs', 'EPSG:3857'),
                proj_data.get('elevation')
            )

        return cls(
            id=data['id'],
            test_pixel=test_pixel,
            reference_pixel=ref_pixel,
            geographic=geographic,
            projected=projected,
            error=data.get('error'),
            enabled=data.get('enabled', True),
            source=data.get('source', 'manual'),
            metadata=data.get('metadata', {})
        )

    def __str__(self) -> str:
        """Return a human-readable string representation of the GCP.

        Returns:
            String showing GCP ID, test pixel, and geographic coordinates.

        Example::

            gcp = GCP(id=1, test_pixel=Pixel(100, 200), ...)
            print(gcp)  # "GCP 1: Test(x_px=100.0, y_px=200.0) → Geo(...)"
        """
        return f"GCP {self.id}: Test{self.test_pixel} → Geo{self.geographic}"

    def __repr__(self) -> str:
        """Return a detailed string representation for debugging.

        Returns:
            String showing all GCP attributes.
        """
        status = "enabled" if self.enabled else "disabled"
        error_str = f", error={self.error:.2f}" if self.error is not None else ""
        return (f"GCP(id={self.id}, test_pixel={self.test_pixel}, "
                f"reference_pixel={self.reference_pixel}, geographic={self.geographic}, "
                f"projected={self.projected}, status={status}{error_str})")
