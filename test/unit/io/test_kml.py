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
#    File:    test_kml.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Unit tests for KML writer and geometry classes.
"""

import pytest

from tmns.io.kml import (
    Altitude_Mode,
    Color_Mode,
    Color_Value,
    Document,
    Folder,
    Line_String,
    Placemark,
    Point,
    Polygon,
    Writer,
)


class TestColor_Value:
    """Test Color_Value class."""

    def test_color_constants(self):
        """Test predefined color constants."""
        assert Color_Value.BLACK == 'ff000000'
        assert Color_Value.WHITE == 'ffffffff'
        assert Color_Value.RED == 'ff0000ff'
        assert Color_Value.GREEN == 'ff00ff00'
        assert Color_Value.BLUE == 'ffff0000'

    def test_from_rgba_components(self):
        """Test conversion from separate RGBA components."""
        # Full opacity red
        result = Color_Value.from_rgba(255, 0, 0, 255)
        assert result == 'FF0000FF'

        # Semi-transparent green
        result = Color_Value.from_rgba(0, 255, 0, 128)
        assert result == '8000FF00'

        # Zero alpha blue
        result = Color_Value.from_rgba(0, 0, 255, 0)
        assert result == '00FF0000'

    def test_from_rgba_integer(self):
        """Test conversion from single RGBA integer."""
        # 0xFF0000FF = red, full opacity
        result = Color_Value.from_rgba(0xFF0000FF)
        assert result == 'FF0000FF'

        # 0x80FF0000 = green, 50% opacity
        result = Color_Value.from_rgba(0x80FF0000)
        assert result == '80FF0000'

        # 0x0000FFFF = blue, zero opacity
        result = Color_Value.from_rgba(0x0000FFFF)
        assert result == '0000FFFF'


class TestColor_Mode:
    """Test Color_Mode enumeration."""

    def test_to_string(self):
        """Test conversion to string."""
        assert Color_Mode.to_string(Color_Mode.NORMAL) == 'normal'
        assert Color_Mode.to_string(Color_Mode.RANDOM) == 'random'

    def test_from_string(self):
        """Test conversion from string."""
        assert Color_Mode.from_string('normal') == Color_Mode.NORMAL
        assert Color_Mode.from_string('random') == Color_Mode.RANDOM
        assert Color_Mode.from_string('NORMAL') == Color_Mode.NORMAL
        assert Color_Mode.from_string('RANDOM') == Color_Mode.RANDOM

    def test_invalid_string(self):
        """Test invalid string raises exception."""
        with pytest.raises(ValueError):
            Color_Mode.from_string('invalid')


class TestAltitude_Mode:
    """Test Altitude_Mode enumeration."""

    def test_to_string(self):
        """Test conversion to string."""
        assert Altitude_Mode.to_string(Altitude_Mode.CLAMP_TO_GROUND) == 'clampToGround'
        assert Altitude_Mode.to_string(Altitude_Mode.RELATIVE_TO_GROUND) == 'relativeToGround'
        assert Altitude_Mode.to_string(Altitude_Mode.ABSOLUTE) == 'absolute'

    def test_from_string(self):
        """Test conversion from string."""
        assert Altitude_Mode.from_string('clamptoground') == Altitude_Mode.CLAMP_TO_GROUND
        assert Altitude_Mode.from_string('relativetoground') == Altitude_Mode.RELATIVE_TO_GROUND
        assert Altitude_Mode.from_string('absolute') == Altitude_Mode.ABSOLUTE
        assert Altitude_Mode.from_string('clampToGround') == Altitude_Mode.CLAMP_TO_GROUND

    def test_invalid_string(self):
        """Test invalid string raises exception."""
        with pytest.raises(ValueError):
            Altitude_Mode.from_string('invalid')


class TestPoint:
    """Test Point geometry class."""

    def test_point_creation(self):
        """Test basic point creation."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        assert point.lat_degrees == 35.0
        assert point.lon_degrees == -118.0
        assert point.elev_m is None
        assert point.alt_mode is None

    def test_point_with_elevation(self):
        """Test point with elevation."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0, elev_m=1500.0)
        assert point.elev_m == 1500.0

    def test_point_with_altitude_mode(self):
        """Test point with altitude mode."""
        point = Point(
            lat_degrees=35.0,
            lon_degrees=-118.0,
            elev_m=1500.0,
            alt_mode=Altitude_Mode.ABSOLUTE
        )
        assert point.alt_mode == Altitude_Mode.ABSOLUTE

    def test_kml_simple(self):
        """Test simple KML coordinate output."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        result = point.kml_simple()
        assert result == '-118.0,35.0,0'

        point = Point(lat_degrees=35.0, lon_degrees=-118.0, elev_m=1500.0)
        result = point.kml_simple()
        assert result == '-118.0,35.0,1500.0'

    def test_kml_output(self):
        """Test full KML output."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0, elev_m=1500.0)
        result = point.kml()

        # Check key components
        assert '<Point>' in result
        assert '<coordinates>' in result
        assert '-118.0,35.0,1500.0' in result
        assert '</coordinates>' in result
        assert '</Point>' in result


class TestLine_String:
    """Test Line_String geometry class."""

    def test_empty_line_string(self):
        """Test empty line string."""
        line = Line_String()
        assert line.coordinates == []

    def test_line_string_with_points(self):
        """Test line string with points."""
        points = [
            Point(lat_degrees=35.0, lon_degrees=-118.0),
            Point(lat_degrees=36.0, lon_degrees=-117.0),
            Point(lat_degrees=37.0, lon_degrees=-116.0),
        ]
        line = Line_String(points=points)
        assert len(line.coordinates) == 3

    def test_line_string_with_altitude_mode(self):
        """Test line string with altitude mode."""
        line = Line_String(altitude_mode=Altitude_Mode.CLAMP_TO_GROUND)
        assert line.altitude_mode == Altitude_Mode.CLAMP_TO_GROUND

    def test_kml_output(self):
        """Test KML output."""
        points = [
            Point(lat_degrees=35.0, lon_degrees=-118.0, elev_m=1000.0),
            Point(lat_degrees=36.0, lon_degrees=-117.0, elev_m=1200.0),
        ]
        line = Line_String(points=points, altitude_mode=Altitude_Mode.RELATIVE_TO_GROUND)
        result = line.kml()

        assert '<LineString>' in result
        assert '<altitudeMode>relativeToGround</altitudeMode>' in result
        assert '<coordinates>' in result
        assert '-118.0,35.0,1000' in result
        assert '-117.0,36.0,1200' in result
        assert '</coordinates>' in result
        assert '</LineString>' in result


class TestPolygon:
    """Test Polygon geometry class."""

    def test_empty_polygon(self):
        """Test empty polygon."""
        poly = Polygon()
        assert len(poly.outerPoints) == 0
        assert len(poly.innerPoints) == 0

    def test_polygon_with_outer_boundary(self):
        """Test polygon with outer boundary."""
        outer = [
            Point(lat_degrees=35.0, lon_degrees=-118.0),
            Point(lat_degrees=35.0, lon_degrees=-117.0),
            Point(lat_degrees=36.0, lon_degrees=-117.0),
            Point(lat_degrees=36.0, lon_degrees=-118.0),
        ]
        poly = Polygon(outer_points=outer)
        assert len(poly.outerPoints) == 4

    def test_polygon_with_inner_boundary(self):
        """Test polygon with inner boundary (hole)."""
        outer = [
            Point(lat_degrees=35.0, lon_degrees=-118.0),
            Point(lat_degrees=35.0, lon_degrees=-117.0),
            Point(lat_degrees=36.0, lon_degrees=-117.0),
            Point(lat_degrees=36.0, lon_degrees=-118.0),
        ]
        inner = [
            Point(lat_degrees=35.2, lon_degrees=-117.8),
            Point(lat_degrees=35.2, lon_degrees=-117.2),
            Point(lat_degrees=35.8, lon_degrees=-117.2),
            Point(lat_degrees=35.8, lon_degrees=-117.8),
        ]
        poly = Polygon(outer_points=outer, inner_points=inner)
        assert len(poly.outerPoints) == 4
        assert len(poly.innerPoints) == 4


class TestPlacemark:
    """Test Placemark feature class."""

    def test_placemark_creation(self):
        """Test basic placemark creation."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        placemark = Placemark(name="Test Point", geometry=point)
        assert placemark.name == "Test Point"
        assert placemark.geometry == point

    def test_placemark_with_all_attributes(self):
        """Test placemark with all attributes."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        placemark = Placemark(
            name="Test Point",
            description="A test point",
            visibility=True,
            style_url="#style1",
            geometry=point
        )
        assert placemark.name == "Test Point"
        assert placemark.description == "A test point"
        assert placemark.visibility is True
        assert placemark.style_url == "#style1"

    def test_placemark_kml_output(self):
        """Test placemark KML output."""
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        placemark = Placemark(name="Test Point", geometry=point)
        result = placemark.kml()

        assert '<Placemark>' in result
        assert '<name>Test Point</name>' in result
        assert '<Point>' in result
        assert '<coordinates>' in result
        assert '-118.0,35.0' in result
        assert '</Placemark>' in result


class TestFolder:
    """Test Folder container class."""

    def test_empty_folder(self):
        """Test empty folder."""
        folder = Folder("Test Folder")
        assert folder.name == "Test Folder"
        assert len(folder.features) == 0

    def test_folder_with_features(self):
        """Test folder with features."""
        point1 = Point(lat_degrees=35.0, lon_degrees=-118.0)
        point2 = Point(lat_degrees=36.0, lon_degrees=-117.0)
        placemark1 = Placemark(name="Point 1", geometry=point1)
        placemark2 = Placemark(name="Point 2", geometry=point2)

        folder = Folder("Test Folder", features=[placemark1, placemark2])
        assert len(folder.features) == 2

    def test_append_node(self):
        """Test adding nodes to folder."""
        folder = Folder("Test Folder")
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        placemark = Placemark(name="Test Point", geometry=point)

        folder.append_node(placemark)
        assert len(folder.features) == 1
        assert folder.features[0] == placemark


class TestDocument:
    """Test Document container class."""

    def test_document_creation(self):
        """Test document creation."""
        doc = Document("Test Document")
        assert doc.name == "Test Document"
        assert len(doc.features) == 0


class TestWriter:
    """Test KML Writer class."""

    def test_writer_creation(self):
        """Test writer creation."""
        writer = Writer()
        assert writer.document is not None
        assert isinstance(writer.document, Document)

    def test_writer_with_path(self):
        """Test writer with output path."""
        writer = Writer("/tmp/test.kml")
        assert writer.output_pathname == "/tmp/test.kml"

    def test_add_node(self):
        """Test adding nodes to writer."""
        writer = Writer()
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        placemark = Placemark(name="Test Point", geometry=point)

        writer.add_node(placemark)
        assert len(writer.document.features) == 1

    def test_add_nodes(self):
        """Test adding multiple nodes."""
        writer = Writer()
        point1 = Point(lat_degrees=35.0, lon_degrees=-118.0)
        point2 = Point(lat_degrees=36.0, lon_degrees=-117.0)
        placemark1 = Placemark(name="Point 1", geometry=point1)
        placemark2 = Placemark(name="Point 2", geometry=point2)

        writer.add_nodes([placemark1, placemark2])
        assert len(writer.document.features) == 2

    def test_to_string(self):
        """Test KML string output."""
        writer = Writer()
        point = Point(lat_degrees=35.0, lon_degrees=-118.0)
        placemark = Placemark(name="Test Point", geometry=point)
        writer.add_node(placemark)

        result = writer.to_string()

        # Check KML structure
        assert result.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert '<kml xmlns="http://www.opengis.net/kml/2.2">' in result
        assert '<Document>' in result
        assert '<Placemark>' in result
        assert '<name>Test Point</name>' in result
        assert '<Point>' in result
        assert '<coordinates>' in result
        assert '-118.0,35.0' in result  # No elevation when None
        assert result.endswith('</kml>\n')

    def test_complex_document(self):
        """Test complex document with folder and multiple placemarks."""
        writer = Writer()

        # Create folder with two points
        point1 = Point(lat_degrees=35.0, lon_degrees=-118.0)
        point2 = Point(lat_degrees=36.0, lon_degrees=-117.0)
        placemark1 = Placemark(name="Point 1", geometry=point1)
        placemark2 = Placemark(name="Point 2", geometry=point2)

        folder = Folder("Test Folder", features=[placemark1, placemark2])
        writer.add_node(folder)

        result = writer.to_string()

        assert '<Folder>' in result
        assert '<name>Test Folder</name>' in result
        assert '<Placemark>' in result
        assert '<name>Point 1</name>' in result
        assert '<name>Point 2</name>' in result
