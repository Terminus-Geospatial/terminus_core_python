#!/usr/bin/env python3
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
#    File:    tmns_gcp_simulator.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Pinhole camera simulator for generating realistic Ground Control Points (GCPs).
"""

import argparse
import json
import logging
import math
from typing import List, Tuple
import numpy as np

# Third-Party Libraries
from dataclasses import dataclass
from scipy.spatial.transform import Rotation

# Project Libraries
from tmns.io.kml import Writer, Document, Folder, Placemark, Point, Style, Line_Style, Poly_Style
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.ecef import ECEF
from tmns.geo.coord.pixel import Pixel
from tmns.geo.coord.transformer import Transformer
from tmns.geo.datum import WGS84
from tmns.geo.ltp import Local_Tangent_Plane


@dataclass
class Camera_Intrinsics:
    """Pinhole camera intrinsic parameters."""

    # Image dimensions
    width: int = 4096
    height: int = 4096

    # Focal length (meters) - standard SI unit
    focal_length: float = 0.056  # 56mm focal length for good coverage at 18K ft

    # Principal point (optical center)
    cx: float = 2048.0  # Principal point x-coordinate (pixels)
    cy: float = 2048.0  # Principal point y-coordinate (pixels)

    # Pixel size (meters) - for converting focal length to pixels
    pixel_size_x: float = 5e-6  # 5 microns
    pixel_size_y: float = 5e-6  # 5 microns

    @property
    def fx(self) -> float:
        """Get focal length in x direction (pixels)."""
        return self.focal_length / self.pixel_size_x

    @property
    def fy(self) -> float:
        """Get focal length in y direction (pixels)."""
        return self.focal_length / self.pixel_size_y

    @property
    def fov_horizontal_deg(self) -> float:
        """Get horizontal field of view in degrees."""
        sensor_width_m = self.width * self.pixel_size_x
        return math.degrees(2 * math.atan(sensor_width_m / (2 * self.focal_length)))

    @property
    def fov_vertical_deg(self) -> float:
        """Get vertical field of view in degrees."""
        sensor_height_m = self.height * self.pixel_size_y
        return math.degrees(2 * math.atan(sensor_height_m / (2 * self.focal_length)))

    def ground_swath_m(self, altitude_m: float) -> float:
        """Get ground swath width at given altitude in meters."""
        return 2 * altitude_m * math.tan(math.radians(self.fov_horizontal_deg / 2))

    def pixel_to_platform(self, pixel: Pixel) -> np.ndarray:
        """
        Convert pixel coordinates to platform coordinates using flight-forward convention.

        Platform coordinate system: X=front, Y=right, Z=bottom (FRB frame)
        Image coordinate system: X=right, Y=down (pixel coordinates)

        1. Pixel to Imager: Convert pixels to physical coordinates on focal plane (meters)
        2. Imager to Camera: Remove distortion and set z = focal_length
        3. Camera to Platform: Use flight-forward convention

        Args:
            pixel: 2D pixel coordinates

        Returns:
            3D point in platform coordinates [front, right, bottom] in meters
        """
        # Step 1: Pixel to Imager (physical coordinates on focal plane in meters)
        # Convert from pixel coordinates to physical meters on focal plane
        # Center the coordinates and scale by pixel size
        x_imager = (pixel.x_px - self.cx) * self.pixel_size_x  # Image X (right)
        y_imager = (pixel.y_px - self.cy) * self.pixel_size_y  # Image Y (down)

        # Step 2: Imager to Camera (no distortion for our simple model)
        # Set z = focal_length to position point at focal plane distance
        x_camera = x_imager   # Camera X (right)
        y_camera = y_imager   # Camera Y (down)
        z_camera = self.focal_length  # Camera Z (forward, along optical axis)

        # Step 3: Camera to Platform (flight-forward convention)
        # Platform: X=front, Y=right, Z=bottom
        # Camera:   X=right, Y=down, Z=forward
        # For flight-forward: principal point projects to (1, 0, 0)
        x_platform = z_camera   # Platform front = Camera forward (focal length)
        y_platform = x_camera   # Platform right = Camera right
        z_platform = -y_camera  # Platform bottom = -Camera down (negative for down)

        return np.array([x_platform, y_platform, z_platform])


@dataclass
class Extrinsic_Params:
    """Camera extrinsic parameters (position and orientation)."""

    # Position in ECEF coordinates (meters)
    position_ecef: ECEF

    # Original lat/lon/alt for reference
    latitude: float  # Degrees
    longitude: float  # Degrees
    altitude: float  # Meters above ground

    # Orientation in ZYX Euler angles (degrees)
    yaw: float    # Rotation about Z-axis (heading)
    pitch: float  # Rotation about Y-axis (elevation/tilt)
    roll: float   # Rotation about X-axis (bank)

    @staticmethod
    def from_lat_lon_alt(latitude: float, longitude: float, altitude: float,
                        yaw: float = 0.0, pitch: float = -90.0, roll: float = 0.0) -> 'Extrinsic_Params':
        """Create extrinsic parameters from lat/lon/alt."""
        # Convert to ECEF
        transformer = Transformer()
        geo = Geographic.create(latitude, longitude, altitude)
        ecef = transformer.geo_to_ecef(geo)

        return Extrinsic_Params(
            position_ecef=ecef,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            yaw=yaw,
            pitch=pitch,
            roll=roll
        )

    def platform_to_enu(self, platform_point: np.ndarray) -> np.ndarray:
        """
        Convert platform coordinates to ENU coordinates.

        Platform coordinate system: X=front, Y=right, Z=bottom (FRB frame)
        ENU coordinate system: East, North, Up (earth frame)

        For nadir pointing (pitch=-90°), we apply the aircraft attitude rotation
        to transform from platform to ENU coordinates, then extend to ground distance.

        Args:
            platform_point: 3D point in platform coordinates [front, right, bottom]

        Returns:
            ENU coordinates [east, north, up] in meters
        """
        # Convert platform coordinates to ENU coordinates
        # Order matters: rotate in platform frame first, then convert to ENU
        # platform2enu maps: front->North, right->East, bottom->Down
        platform2enu = np.array([[ 0, 1,  0 ],
                                 [ 1, 0,  0 ],
                                 [ 0, 0, -1 ]])

        # Apply rotation matrix for aircraft attitude to platform coordinates
        R = self._rotation_matrix_from_euler(self.yaw, self.pitch, self.roll)

        # Transform: rotate in platform frame, then convert to ENU
        enu_direction = platform2enu @ (R @ platform_point)

        return enu_direction

    def _rotation_matrix_from_euler(self, yaw: float, pitch: float, roll: float) -> np.ndarray:
        """
        Create rotation matrix from ZYX Euler angles using scipy.

        Args:
            yaw: Rotation about Z-axis (degrees)
            pitch: Rotation about Y-axis (degrees)
            roll: Rotation about X-axis (degrees)

        Returns:
            3x3 rotation matrix
        """
        # Convert to radians
        yaw_rad = math.radians(yaw)
        pitch_rad = math.radians(pitch)
        roll_rad = math.radians(roll)

        # Use scipy's Rotation.from_euler with ZYX order
        print( 'Yaw: ', yaw_rad, ', Pitch: ', pitch_rad, ', Roll: ', roll_rad)
        rotation = Rotation.from_euler('ZYX', [yaw_rad, pitch_rad, roll_rad], degrees=False)

        return rotation.as_matrix()


@dataclass
class Ground_Control_Point:
    """Ground Control Point with image and world coordinates."""
    pixel: Pixel
    world: ECEF
    name: str | None = None


class Pinhole_Camera:
    """Pinhole camera model for perspective projection."""

    def __init__(self, intrinsics: Camera_Intrinsics):
        """Initialize camera with intrinsic parameters."""
        self.intrinsics = intrinsics

        # Build intrinsic matrix K
        self.K = np.array([
            [intrinsics.fx, 0.0, intrinsics.cx],
            [0.0, intrinsics.fy, intrinsics.cy],
            [0.0, 0.0, 1.0]
        ])

    def project_to_ground(self, pixel: Pixel, extrinsic: Extrinsic_Params, datum: WGS84) -> Geographic:
        """
        Project a pixel coordinate to ground coordinates using the datum's ray intersection.

        Transformation chain: pixel -> platform -> ENU -> ECEF -> ray intersection -> geographic

        Args:
            pixel: 2D pixel coordinates
            extrinsic: Camera extrinsic parameters
            datum: Geodetic datum for ground intersection

        Returns:
            Geographic coordinates on ground surface
        """

        logger = logging.getLogger(__name__)
        # Step 1: Convert pixel to platform coordinates (direction vector)
        platform_point = self.intrinsics.pixel_to_platform(pixel)
        logger.info(f"Platform point: {platform_point}")

        # Step 2: Convert platform direction vector to ENU coordinates
        enu_point = extrinsic.platform_to_enu(platform_point)
        logger.info(f"ENU point: {enu_point}")

        # Step 3: Convert ENU direction vector to ECEF direction
        ref_geo = Geographic.create(extrinsic.latitude, extrinsic.longitude, 0.0)
        rot_matrix = Local_Tangent_Plane.enu_to_ecef_matrix(ref_geo, 3)
        ray_direction = rot_matrix @ enu_point
        logger.info(f"Ray direction ECEF: {ray_direction}")

        # Step 4: Get camera position in ECEF
        camera_ecef = extrinsic.position_ecef.to_array()
        logger.info(f"Camera ECEF: {camera_ecef}")
        logger.info(f"Ray direction: {ray_direction}")

        # Step 5: Find intersection with ellipsoid using datum function
        # Normalize direction for numerical stability
        ray_direction_norm = ray_direction / np.linalg.norm(ray_direction)
        ground_point = datum.ray_ellipsoid_intersection(
            origin=camera_ecef,
            direction=ray_direction_norm
        )
        logger.info(f"Ground point: {ground_point}")

        return ground_point


class GCP_Simulator:
    """Main simulator class for generating Ground Control Points."""

    def __init__(self, camera: Pinhole_Camera, extrinsic: Extrinsic_Params):
        """
        Initialize simulator.

        Args:
            camera: Pinhole camera model
            extrinsic: Camera position and orientation
        """
        self.camera = camera
        self.extrinsic = extrinsic

    def generate_gcps(self, points_x: int = 10, points_y: int = 10, verbose: bool = False) -> List[Ground_Control_Point]:
        """
        Generate GCPs in a regular pixel grid pattern with specified number of points.

        Args:
            points_x: Number of grid points in x direction
            points_y: Number of grid points in y direction
            verbose: Enable verbose logging

        Returns:
            List of Ground Control Points
        """
        logger = logging.getLogger(__name__)

        # Create datum for ground intersection
        datum = WGS84()

        # Generate pixel grid
        gcps = []
        gcp_id = 0

        # Calculate spacing
        x_spacing = self.camera.intrinsics.width / (points_x - 1)
        y_spacing = self.camera.intrinsics.height / (points_y - 1)

        if verbose:
            logger.debug(f"Generating {points_x}x{points_y} pixel grid")
            logger.debug(f"X spacing: {x_spacing} pixels, Y spacing: {y_spacing} pixels")

        # Generate grid points
        for i in range(points_x):
            for j in range(points_y):
                # Calculate pixel coordinates
                x = i * x_spacing
                y = j * y_spacing

                pixel = Pixel(x_px=x, y_px=y)

                try:
                    # Project pixel to ground
                    ground_geo = self.camera.project_to_ground(pixel, self.extrinsic, datum)

                    # Convert Geographic to ECEF using Transformer
                    transformer = Transformer()
                    ground_ecef = transformer.geo_to_ecef(ground_geo)

                    # Create GCP
                    gcp = Ground_Control_Point(
                        pixel=pixel,
                        world=ground_ecef,
                        name=f"GCP_{gcp_id:03d}"
                    )
                    gcps.append(gcp)
                    gcp_id += 1

                except ValueError as e:
                    # Ray does not intersect Earth (e.g., horizontal flight, behind camera)
                    logger.debug(f"Skipping pixel ({int(round(x))}, {int(round(y))}) - no ground intersection: {e}")
                    continue

        return gcps

    def export_to_json(self, gcps: List[Ground_Control_Point], filename: str) -> None:
        """
        Export GCPs to JSON file.

        Args:
            gcps: List of Ground Control Points
            filename: Output JSON filename
        """
        # Convert GCPs to dictionary format
        gcp_data = {
            "metadata": {
                "camera": {
                    "width": self.camera.intrinsics.width,
                    "height": self.camera.intrinsics.height,
                    "focal_length": {
                        "fx": self.camera.intrinsics.fx,
                        "fy": self.camera.intrinsics.fy
                    },
                    "principal_point": {
                        "cx": self.camera.intrinsics.cx,
                        "cy": self.camera.intrinsics.cy
                    }
                },
                "extrinsic": {
                    "latitude": self.extrinsic.latitude,
                    "longitude": self.extrinsic.longitude,
                    "altitude": self.extrinsic.altitude,
                    "yaw": self.extrinsic.yaw,
                    "pitch": self.extrinsic.pitch,
                    "roll": self.extrinsic.roll
                },
                "ground_plane": {
                    "method": "datum_intersection"
                }
            },
            "gcps": []
        }

        # Add GCPs
        for gcp in gcps:
            gcp_dict = {
                "name": gcp.name,
                "pixel": {
                    "x": gcp.pixel.x_px,
                    "y": gcp.pixel.y_px
                },
                "world": {
                    "x": gcp.world.x_m,
                    "y": gcp.world.y_m,
                    "z": gcp.world.z_m
                }
            }
            gcp_data["gcps"].append(gcp_dict)

        # Write to file
        with open(filename, 'w') as f:
            json.dump(gcp_data, f, indent=2)

    def export_to_kml(self, gcps: List[Ground_Control_Point], filename: str) -> None:
        """
        Export GCPs to KML file.

        Args:
            gcps: List of Ground Control Points
            filename: Output KML filename
        """
        # Create KML document
        writer = Writer()

        # Create main folder
        folder = Folder("Ground Control Points")

        # Create styles for GCPs
        point_style = Style(id="gcp_point")
        point_style.icon_style = None  # Will use default
        point_style.label_style = None

        # Add style to document
        writer.add_node(point_style)

        # Add GCPs as placemarks
        transformer = Transformer()
        for gcp in gcps:
            # Convert ECEF world coordinates to geographic using accurate transformation
            geo_point = transformer.ecef_to_geo(gcp.world)

            # Create placemark
            placemark = Placemark(
                name=gcp.name or f"GCP",
                description=f"Pixel: ({gcp.pixel.x_px:.1f}, {gcp.pixel.y_px:.1f})\\n"
                           f"World: ({gcp.world.x_m:.1f}, {gcp.world.y_m:.1f}, {gcp.world.z_m:.1f})\\n"
                           f"Lat/Lon: ({geo_point.latitude_deg:.6f}°, {geo_point.longitude_deg:.6f}°)",
                style_url="#gcp_point"
            )

            # Create point geometry with accurate geographic coordinates
            point_geom = Point(
                lat_degrees=geo_point.latitude_deg,
                lon_degrees=geo_point.longitude_deg,
                elev_m=geo_point.altitude_m
            )

            placemark.geometry = point_geom
            folder.append_node(placemark)

        # Add folder to document
        writer.add_node(folder)

        # Write KML file
        writer.write(filename)


def create_standard_simulator() -> GCP_Simulator:
    """
    Create a simulator with standard parameters using ECEF coordinates.

    Returns:
        Configured GCP simulator
    """
    # Standard camera intrinsics
    intrinsics = Camera_Intrinsics(
        width=4096,
        height=4096,
        fx=2000.0,  # ~10mm focal length for 5 micron pixels
        fy=2000.0,
        cx=2048.0,  # Center of image
        cy=2048.0
    )

    # Create camera
    camera = Pinhole_Camera(intrinsics)

    # Standard extrinsic: 18,000 ft altitude, nadir pointing over Bakersfield, CA
    extrinsic = Extrinsic_Params.from_lat_lon_alt(
        latitude=35.3733,     # Bakersfield, CA latitude
        longitude=-119.0187,  # Bakersfield, CA longitude
        altitude=5486.4,      # 18,000 feet in meters
        yaw=0.0,             # North pointing
        pitch=0.0,         # Straight down (nadir)
        roll=0.0             # Level wings
    )

    # Ground plane centered at Bakersfield
    bakersfield_geo = Geographic.create(35.3733, -119.0187, 0.0)
    ground = Ground_Plane(size=2000.0, center_geo=bakersfield_geo)  # 2km x 2km ground area

    return GCP_Simulator(camera, extrinsic, ground)


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_format = '%(levelname)s - %(filename)s:%(lineno)d - %(message)s'

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[console_handler],
        force=True
    )

    return logging.getLogger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate Ground Control Points (GCPs) using pinhole camera model",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # Camera parameters
    parser.add_argument("--width", type=int, default=4096,
                       help="Image width in pixels")
    parser.add_argument("--height", type=int, default=4096,
                       help="Image height in pixels")
    parser.add_argument("--focal-length", type=float, default=0.056,
                       help="Focal length in meters")
    parser.add_argument("--cx", type=float, default=2048.0,
                       help="Principal point x-coordinate (pixels)")
    parser.add_argument("--cy", type=float, default=2048.0,
                       help="Principal point y-coordinate (pixels)")

    # Camera position
    parser.add_argument("--latitude", type=float, default=35.3733,
                       help="Camera latitude (degrees)")
    parser.add_argument("--longitude", type=float, default=-119.0187,
                       help="Camera longitude (degrees)")
    parser.add_argument("--altitude", type=float, default=5486.4,
                       help="Camera altitude (meters)")
    parser.add_argument("--yaw", type=float, default=0.0,
                       help="Camera yaw (degrees)")
    parser.add_argument("--pitch", type=float, default=-90.0,
                       help="Camera pitch (degrees)")
    parser.add_argument("--roll", type=float, default=0.0,
                       help="Camera roll (degrees)")

    # GCP generation
    parser.add_argument("--grid-points-x", type=int, default=10,
                       help="Number of grid points in x direction")
    parser.add_argument("--grid-points-y", type=int, default=10,
                       help="Number of grid points in y direction")

    # Output
    parser.add_argument("--json-output", default="gcps.json",
                       help="Output JSON filename")
    parser.add_argument("--kml-output", default="gcps.kml",
                       help="Output KML filename")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable debug logging (DEBUG level)")

    return parser.parse_args()


def create_simulator(args: argparse.Namespace) -> GCP_Simulator:
    """Create simulator from command line arguments."""
    # Camera intrinsics
    intrinsics = Camera_Intrinsics(
        width=args.width,
        height=args.height,
        focal_length=args.focal_length,
        cx=args.cx,
        cy=args.cy
    )

    # Create camera
    camera = Pinhole_Camera(intrinsics)

    # Camera extrinsic
    extrinsic = Extrinsic_Params.from_lat_lon_alt(
        latitude=args.latitude,
        longitude=args.longitude,
        altitude=args.altitude,
        yaw=args.yaw,
        pitch=args.pitch,
        roll=args.roll
    )

    return GCP_Simulator(camera, extrinsic)


def main():
    """Main function to demonstrate the simulator."""
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(args.verbose)

    logger.info("Creating GCP Simulator...")
    logger.info(f"Camera: {args.width}x{args.height}")
    logger.info(f"Focal length: {args.focal_length*1000:.1f} mm ({args.focal_length} m)")

    # Create intrinsics to calculate FOV
    intrinsics = Camera_Intrinsics(
        width=args.width,
        height=args.height,
        focal_length=args.focal_length
    )
    logger.info(f"Field of View: {intrinsics.fov_horizontal_deg:.1f}° H x {intrinsics.fov_vertical_deg:.1f}° V")
    logger.info(f"Ground swath at {args.altitude:.0f}m: {intrinsics.ground_swath_m(args.altitude):.0f}m")

    logger.info(f"Altitude: {args.altitude:.1f} m")
    logger.info(f"Orientation: Yaw={args.yaw}°, Pitch={args.pitch}°, Roll={args.roll}°")
    logger.info(f"Grid points: {args.grid_points_x} x {args.grid_points_y}")

    # Create simulator
    simulator = create_simulator(args)

    # Generate GCPs
    logger.info(f"Generating grid GCPs...")

    # Generate grid with specified number of points
    gcps = simulator.generate_gcps(
        points_x=args.grid_points_x,
        points_y=args.grid_points_y,
        verbose=args.verbose
    )

    logger.info(f"Generated {len(gcps)} GCPs")

    # Show first few GCPs
    for i, gcp in enumerate(gcps[:5]):
        logger.debug(f"  {gcp.name}: Pixel({gcp.pixel.x_px:.1f}, {gcp.pixel.y_px:.1f}) -> "
                    f"World({gcp.world.x_m:.6f}, {gcp.world.y_m:.6f}, {gcp.world.z_m:.6f})")

    if len(gcps) > 5:
        logger.debug(f"  ... and {len(gcps) - 5} more")

    # Export to JSON and KML
    logger.info(f"Exporting to {args.json_output}...")
    simulator.export_to_json(gcps, args.json_output)

    logger.info(f"Exporting to {args.kml_output}...")
    simulator.export_to_kml(gcps, args.kml_output)

    logger.info(f"Done! Files saved: {args.json_output}, {args.kml_output}")
    if not args.verbose:
        print(f"Generated {len(gcps)} GCPs")


if __name__ == "__main__":
    main()