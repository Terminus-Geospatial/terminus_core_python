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
#    File:    kml.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
KML writer and geometry classes for generating KML documents.
"""

class Color_Value:
    BLACK           = 'ff000000'
    BLUE            = 'ffff0000'
    BLUE_GRAY       = 'ffc7af98'
    BROWN           = 'ff2a2aa5'
    CRIMSON         = 'ff35229d'
    CYAN            = 'ffffff00'
    DARK_SLATE_BLUE = 'f0ff0000'
    GREEN           = 'ff00ff00'
    OLIVE_GREEN     = 'ff2e716d'
    ORANGE          = 'ff00a5ff'
    PLATINUM        = 'ffe2e4e5'
    PURPLE          = 'ff800080'
    RED             = 'ff0000ff'
    WHITE           = 'ffffffff'

    @staticmethod
    def from_rgba(r, g=None, b=None, a=None):
        """
        Convert RGBA color to KML color format (AABBGGRR).

        Supports two calling patterns:
        - from_rgba(r, g, b, a) - separate components (0-255)
        - from_rgba(rgba) - single RGBA integer value

        Args:
            r: Red component (0-255) or full RGBA integer
            g: Green component (0-255) or None if r is RGBA integer
            b: Blue component (0-255) or None if r is RGBA integer
            a: Alpha component (0-255) or None if r is RGBA integer

        Returns:
            KML color string in AABBGGRR format
        """
        # If only r is provided, treat it as a full RGBA value
        if g is None and b is None and a is None:
            rgba = r
            a = (rgba >> 24) & 0xFF
            b = (rgba >> 16) & 0xFF
            g = (rgba >> 8) & 0xFF
            r = rgba & 0xFF

        # Return KML color format: AABBGGRR
        return f'{a:02X}{b:02X}{g:02X}{r:02X}'

class Color_Mode:

    NORMAL=1
    RANDOM=2

    @staticmethod
    def to_string(mode):
        if mode == Color_Mode.NORMAL:
            return 'normal'
        if mode == Color_Mode.RANDOM:
            return 'random'
        raise Exception('Unknown Color Mode')

    @staticmethod
    def from_string(mode):

        val = str(mode).lower()
        if val == 'normal':
            return Color_Mode.NORMAL

        if val == 'random':
            return Color_Mode.RANDOM

        raise Exception('Unknown ColorMode (' + str(mode) + ')')


class Altitude_Mode:

    CLAMP_TO_GROUND=1
    RELATIVE_TO_GROUND=2
    ABSOLUTE=3

    @staticmethod
    def to_string(mode):

        if mode == Altitude_Mode.CLAMP_TO_GROUND:
            return 'clampToGround'
        if mode == Altitude_Mode.RELATIVE_TO_GROUND:
            return 'relativeToGround'
        if mode == Altitude_Mode.ABSOLUTE:
            return 'absolute'
        raise Exception('Unknown Mode')

    @staticmethod
    def from_string(mode):

        val = str(mode).lower()
        if val == 'clamptoground':
            return Altitude_Mode.CLAMP_TO_GROUND

        if val == 'relativetoground':
            return Altitude_Mode.RELATIVE_TO_GROUND

        if val == 'absolute':
            return Altitude_Mode.ABSOLUTE

        raise Exception('Unknown AltitudeMode (' + str(mode) + ')')

class Object:

    #  KML Name
    kml_name = None

    #  ID
    id = None

    def __init__(self, id = None, kml_name = 'Object'):

        #  Set the KML Name
        self.kml_name = kml_name

        #  Set the ID
        self.id = id

    def kml_content(self, offset=0):
        _ = offset  # Used by subclasses for indentation
        return ''


    def kml(self, offset=0):

        #  Create offset str
        gap = ' ' * offset

        #  Create KML Node
        output = ''
        output += gap + '<' + self.kml_name

        if self.id is not None:
            output += ' id="' + self.id + '"'
        output += '>\n'

        #  Add the content
        output += self.kml_content(offset + 2)

        #  Close the KML Node
        output += gap + '</' + self.kml_name + '>\n'

        return output

    def __str__(self, offset = 0):

        gap = ' ' * offset

        #  Create output
        return gap + 'Node: ' + self.kml_name

    #def __repr__(self):
    #    return self.__str__()


class Time_Span(Object):
    """
    KML TimeSpan element for temporal visualization.
    Defines a time period during which a feature is visible.
    Used for animated playback in Google Earth.
    """

    def __init__(self, begin=None, end=None, id=None, kml_name='TimeSpan'):
        """
        Args:
            begin: Begin time as ISO 8601 string or datetime object
            end: End time as ISO 8601 string or datetime object
            id: Optional ID attribute
            kml_name: KML element name (default: 'TimeSpan')
        """
        Object.__init__(self, id=id, kml_name=kml_name)

        # Convert datetime to ISO string if needed
        if hasattr(begin, 'isoformat'):
            self.begin = begin.isoformat()
        else:
            self.begin = begin

        if hasattr(end, 'isoformat'):
            self.end = end.isoformat()
        else:
            self.end = end

    def kml_content(self, offset=0):
        gap = ' ' * offset
        output = ''

        if self.begin is not None:
            output += gap + '<begin>' + str(self.begin) + '</begin>\n'

        if self.end is not None:
            output += gap + '<end>' + str(self.end) + '</end>\n'

        return output


class Style_Selector(Object):

    def __init__(self, id = None, kml_name='StyleSelector'):

        #  Build Parent
        Object.__init__(self, id=id, kml_name=kml_name)


class Sub_Style(Object):

    def __init__(self, id=None, kml_name='SubStyle'):

        #  Build Parent
        Object.__init__(self, id=id, kml_name=kml_name)


class Color_Style(Sub_Style):

    def __init__(self, id=None, color=None, color_mode=None, kml_name='ColorStyle'):

        #  Build Parent
        Sub_Style.__init__(self, id=id, kml_name=kml_name)

        #  Set the Color
        self.color = color
        self.color_mode = color_mode


    def kml_content(self, offset = 0):

        #  Create gap string
        gap = ' ' * offset

        #  Create output
        output = ''

        #  Add parent stuff
        output += Sub_Style.kml_content(self, offset=offset)


        #  Set the Color
        if self.color is not None:
            output += gap + '<color>' + self.color + '</color>\n'


        #  Set the color mode
        if self.color_mode is not None:
            output += gap + '<colorMode>' + Color_Mode.to_string(self.color_mode) + '</colorMode>\n'


        #  Return output
        return output


class Line_Style(Color_Style):

    def __init__( self,
                  id         = None,
                  color: str = None,
                  color_mode = None,
                  width      = None,
                  kml_name   = 'LineStyle' ):

        #  Build Parent
        Color_Style.__init__(self, id=id, color=color, color_mode=color_mode, kml_name=kml_name)

        #  Set the Width and Color
        self.width = width

    def kml_content(self, offset=0):

        #  Create gap string
        gap = ' ' * offset

        #  Create Output
        output = ''

        #  Add Parent stuff
        output += Color_Style.kml_content(self, offset)


        #  Add the LineStyle Specific Items
        if self.width is not None:
            output += gap + '<width>' + str(self.width) + '</width>\n'


        #  Return result
        return output


class Poly_Style(Color_Style):

    def __init__( self,
                  id            = None,
                  color         = None,
                  color_mode    = None,
                  fill: bool    = None,
                  outline: bool = None,
                  kml_name      = 'PolyStyle' ):

        #  Build Parent
        Color_Style.__init__( self,
                              id         = id,
                              color      = color,
                              color_mode = color_mode,
                              kml_name   = kml_name )

        # Set Polygon Attributes
        self.fill = fill
        self.outline = outline

    def kml_content(self, offset=0):
        #  Create gap string
        gap = ' ' * offset

        #  Create Output
        output = ''

        #  Add Parent stuff
        output += Color_Style.kml_content(self, offset)

        #  Add the fill
        if self.fill:
            fval = '1' if self.fill else '0'
            output += gap + '<fill>' + fval + '</fill>\n'

        #  Outline
        if self.outline:
            oval = '1' if self.outline else '0'
            output += gap + '<outline>' + oval + '</outline>\n'


        #  Return result
        return output

class Icon_Style(Color_Style):

    def __init__(self, id=None, color=None, color_mode = None,
                 scale=None, heading=None, icon=None, kml_name='PolyStyle'):

        #  Build Parent
        Color_Style.__init__(self, id=id, color=color, color_mode=color_mode, kml_name=kml_name)

        # Set Polygon Attributes
        self.scale = scale
        self.heading = heading
        self.icon = icon


    def kml_content(self, offset=0):
        #  Create Output
        output = ''

        #  Add Parent stuff
        output += Color_Style.kml_content(self, offset)

        #  Add the


        #  Return result
        return output

class Label_Style(Color_Style):

    def __init__( self,
                  id         = None,
                  color      = None,
                  color_mode = None,
                  scale      = None,
                  kml_name   = 'PolyStyle'):

        #  Build Parent
        Color_Style.__init__( self,
                              id         = id,
                              color      = color,
                              color_mode = color_mode,
                              kml_name   = kml_name)

        # Set Polygon Attributes
        self.scale = scale


    def kml_content(self, offset = 0):

        #  Create Output
        output = ''

        #  Add Parent stuff
        output += Color_Style.kml_content(self, offset)

        #  Add the


        #  Return result
        return output

class Style(Style_Selector):

    def __init__(self, id=None,
                 line_style=None,
                 poly_style=None,
                 icon_style=None,
                 label_style=None,
                 kml_name='Style'):

        #  Create Parent
        Style_Selector.__init__(self, id=id, kml_name=kml_name)

        #  Set styles
        self.line_style = line_style
        self.poly_style = poly_style
        self.icon_style = icon_style
        self.label_style = label_style


    def kml_content(self, offset = 0):

        #  Create output
        output = ''

        #  add parent stuff
        output += Style_Selector.kml_content(self, offset)

        #  Add Line Style
        if self.line_style is not None:
            output += self.line_style.kml( offset=offset)

        #  Add PolyStyle
        if self.poly_style is not None:
            output += self.poly_style.kml( offset=offset)

        #  Add Label Style
        if self.label_style is not None:
            output += self.label_style.kml(offset=offset)

        #  Add Icon Style
        if self.icon_style is not None:
            output += self.icon_style.kml(offset=offset)


        return output


class Feature(Object):

    def __init__(self,
                 id = None,
                 name = None,
                 visibility=None,
                 is_open=None,
                 description=None,
                 style_url=None,
                 time_span=None,
                 kml_name='Feature'):

        #  Construct parent
        Object.__init__(self, id=id, kml_name=kml_name)

        #  Set feature name
        self.name = name
        self.visibility = visibility
        self.is_open = is_open
        self.description = description
        self.style_url = style_url
        self.time_span = time_span


    def kml_content(self, offset = 0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        output = ''

        #  Call parent method
        output += Object.kml_content(self, offset=offset)

        #  Set name
        if self.name is not None:
            output += gap + '<name>' + self.name + '</name>\n'

        #  Set Style URL
        if self.style_url is not None:
            output += gap + '<styleUrl>' + str(self.style_url) + '</styleUrl>\n'

        if self.visibility is not None:
            output += gap + '<visibility>'
            if self.visibility:
                output += '1'
            else:
                output += '0'
            output += '</visibility>\n'

        #  Process the Description
        if self.description is not None:
            output += gap + '<description>' + self.description + '</description>\n'

        #  Add TimeSpan if present
        if self.time_span is not None:
            output += self.time_span.kml(offset)

        return output

    def __str__(self, offset=0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        output = Object.__str__(self, offset) + '\n'

        output += gap + 'Name: ' + str(self.name)

        return output

class Geometry(Object):

    def __init__(self, id = None, kml_name='Geometry'):

        #  Call parent
        Object.__init__(self, id=id, kml_name=kml_name)



class Container(Feature):

    def __init__(self, id = None, features = None, name = None, is_open=None, kml_name='Container'):

        #  Build Parent
        Feature.__init__(self, id=id, name=name, is_open=is_open, kml_name=kml_name)


        #  Set the features
        if features is not None:
            self.features = features
        else:
            self.features = []


    def append_node(self, new_node):
        self.features.append(new_node)


    def find(self, name):

        #  Split the path
        parts = name.strip().split('/')

        #  Check if name is empty or junk
        if len(name) <= 0 or len(parts) <= 0:
            return []

        #  Check if we are at the base level
        if len(parts) == 1:

            # Create output
            output = []

            #  Look over internal features
            for f in self.features:

                #  Check name
                if name == f.name:
                    output.append(f)
            return output


        #  If more than one level, call recursively


        #  Check if base is in node
        output = []
        for f in self.features:

            #  If the item is a container, call recursively
            if f.name == parts[0] and isinstance(f, Container):

                #  Run the query
                res = f.Find('/'.join(map(str,parts[1:])))

                #  Check if we got a list back
                if (res is not None) and isinstance(res, list):
                    output += res

            #  If the item is not a container, skip

        return output

        return []


    def kml_content(self, offset = 0):

        #  Create output
        output = ''

        #  Add parent material
        output += Feature.kml_content(self, offset=offset)

        #  Iterate over internal features
        for feature in self.features:
            #print( f'Processing Feature: {feature.kml_name}' )
            output += feature.kml( offset + 2 )

        #  Return output
        return output


    def __str__(self, offset = 0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        output = gap + Feature.__str__(self, offset) + '\n'

        output += gap + 'Feature Nodes: Size (' + str(len(self.features)) + ')\n'
        for feature in self.features:
            output += gap + str(feature) + '\n'

        return output


class Folder(Container):


    def __init__(self, folder_name,
                 id = None,
                 features = None,
                 is_open=None,
                 kml_name='Folder'):

        #  Construct Parent
        """
        :type kml_name: 'string'
        """
        Container.__init__( self,
                            id       = id,
                            features = features,
                            name     = folder_name,
                            is_open   = is_open,
                            kml_name = kml_name)


    def __str__(self, offset=0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        return gap + Container.__str__(self, offset)


class Document(Container):

    def __init__(self, name=None, id=None, features = None, is_open=None, kml_name='Document'):

        #  Construct the parent
        Container.__init__( self,
                            id = id,
                            features = features,
                            name     = name,
                            is_open   = is_open,
                            kml_name = kml_name )


class Placemark( Feature ):

    def __init__(self,
                 id = None,
                 name = None,
                 visibility=None,
                 is_open=None,
                 description=None,
                 style_url = None,
                 time_span = None,
                 kml_name='Placemark',
                 geometry=None):

        #  Call parent
        Feature.__init__( self,
                          id=id,
                          name=name,
                          visibility=visibility,
                          is_open=is_open,
                          description=description,
                          style_url=style_url,
                          time_span=time_span,
                          kml_name=kml_name)

        #  Set the geometry
        self.geometry = geometry


    def kml_content(self, offset = 0):

        #  Create output
        output = ''

        #  Add parent material
        output += Feature.kml_content(self, offset=offset)

        #  Add Geometry
        if self.geometry is not None:
            output += self.geometry.kml(offset)

        # Return output
        return output


class Point( Geometry ):

    def __init__( self,
                  id = None,
                  lat_degrees = None,
                  lon_degrees = None,
                  elev_m      = None,
                  alt_mode    = None,
                  kml_name    = 'Point'):

        Geometry.__init__(self, id=id, kml_name=kml_name)

        #  Set the coordinates
        self.lat_degrees = lat_degrees
        self.lon_degrees = lon_degrees
        self.elev_m = elev_m
        self.alt_mode = alt_mode

    def kml_simple(self):

        output = str(self.lon_degrees) + ',' + str(self.lat_degrees) + ','
        if self.elev_m is None:
            output += '0'
        else:
            output += str(self.elev_m)
        return output


    def kml_content(self, offset = 0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        output = ''

        #  Add Parent Stuff
        output += Geometry.kml_content(self, offset=offset)

        #  Add the altitude mode
        if self.alt_mode is not None:
            output += gap + '<altitudeMode>' + str(self.alt_mode) + '</altitudeMode>\n'

        #  Add coordinates
        output += gap + '<coordinates>\n'
        output += gap + ' ' + str(self.lon_degrees) + ',' + str(self.lat_degrees)
        if self.elev_m is not None:
            output += ',' + str(self.elev_m)
        output += '\n' + gap + '</coordinates>\n'


        #  Return output
        return output


class Line_String(Geometry):

    def __init__( self,
                  id = None,
                  altitude_mode: Altitude_Mode = None,
                  points = None,
                  kml_name = 'LineString' ):

        #  Build parent
        Geometry.__init__(self, id=id, kml_name=kml_name)

        if altitude_mode is None:
            self.altitude_mode = None
        else:
            self.altitude_mode = altitude_mode

        #  Set points
        if points is None:
            self.coordinates = []
        else:
            self.coordinates = points

    def kml_content(self, offset = 0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        output = ''

        #  Add Parent Stuff
        output += Geometry.kml_content(self, offset=offset)

        if self.altitude_mode is not None:
                output += gap + '<altitudeMode>' + Altitude_Mode.to_string(self.altitude_mode) + '</altitudeMode>\n'

        #  Add the points
        output += gap + '<coordinates>\n'
        for p in self.coordinates:
            output += gap + '   ' + p.kml_simple() + '\n'
        output += gap + '</coordinates>\n'

        return output

class Polygon(Geometry):

    def __init__(self,
                 id = None,
                 altitude_mode: Altitude_Mode = None,
                 inner_points=None,
                 outer_points=None,
                 kml_name="Polygon"):

        #  Build Parent
        Geometry.__init__(self, id=id, kml_name=kml_name)

        if altitude_mode is None:
            self.altitude_mode = None
        else:
            self.altitude_mode = altitude_mode

        #  Set inner points
        if inner_points is None:
            self.innerPoints = []
        else:
            self.innerPoints = inner_points

        #  Set outer points
        if outer_points is None:
            self.outerPoints = []
        else:
            self.outerPoints = outer_points


    def kml_content(self, offset = 0):

        #  Create gap
        gap = ' ' * offset

        #  Create output
        output = ''

        #  Add Parent Stuff
        output += Geometry.kml_content(self, offset=offset)

        if self.altitude_mode is not None:
                output += gap + '<altitudeMode>' + Altitude_Mode.to_string(self.altitude_mode) + '</altitudeMode>\n'

        #  Add the outer loop
        if len(self.outerPoints) > 0:

            #  Add the xml stuff
            output += gap + '<outerBoundaryIs>\n'
            output += gap + '  <LinearRing>\n'
            output += gap + '    <coordinates>\n'

            for p in self.outerPoints:
                output += gap + '   ' + p.kml_simple() + '\n'
            output += gap + '    </coordinates>\n'
            output += gap + '  </LinearRing>\n'
            output += gap + '</outerBoundaryIs>\n'

        #  Add the inner loop
        if len(self.innerPoints) > 0:

            #  Add the xml stuff
            output += gap + '<innerBoundaryIs>\n'
            output += gap + '  <LinearRing>\n'
            output += gap + '    <coordinates>\n'
            output += gap + '       '
            for p in self.innerPoints:
                output += p.kml_simple() + ' '
            output += '\n' + gap + '    </coordinates>\n'
            output += gap + '  </LinearRing>\n'
            output += gap + '</innerBoundaryIs>\n'

        return output

class Multi_Geometry(Geometry):

    def __init__( self,
                  id = None,
                  geometries: list[Geometry] = None,
                  kml_name: str = "MultiGeometry" ) -> None:

        Geometry.__init__(self, id=id, kml_name=kml_name)
        self.geometries = geometries

    def kml_content(self, offset=0):

        #  Create output
        output = ''

        #  Add Parent Stuff
        output += Geometry.kml_content(self, offset=offset)

        for geom in self.geometries:

            output += geom.kml( offset + 4 )

        return output

class Writer:

    #  List of nodes
    nodes = []

    document = None

    def __init__(self, output_pathname = None):

        # Set the output pathname
        self.output_pathname = output_pathname

        #  Default nodes
        self.nodes = []

        self.document = Document()


    def add_node(self, node):

        #  Append to node
        self.document.append_node(node)

    def add_nodes(self, nodes):

        for node in nodes:
            self.add_node(node)


    def to_string(self):

        output  = '<?xml version="1.0" encoding="UTF-8"?>\n'
        output += '<kml xmlns="http://www.opengis.net/kml/2.2">\n'
        output += self.document.kml()
        output += '</kml>\n'
        return output

    def write( self, output_path = None ):

        # Determine output pathname
        if output_path is not None:
            output_pathname = output_path
        elif hasattr(self, 'output_pathname') and self.output_pathname is not None:
            output_pathname = self.output_pathname
        else:
            raise ValueError("No output path specified and no default output_pathname set")

        #  Open file for output
        with open(output_pathname, 'w') as fout:

            fout.write(self.to_string())
