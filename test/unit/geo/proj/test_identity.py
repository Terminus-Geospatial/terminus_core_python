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
#    File:    test_identity.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Unit tests for Identity projector
"""


from tmns.geo.coord import Geographic, Pixel
from tmns.geo.proj import Identity, Transformation_Type


class TestIdentity:
    """Test the identity projection implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.projector = Identity()

    def test_transformation_type(self):
        """Test transformation type property."""
        assert self.projector.transformation_type == Transformation_Type.IDENTITY

    def test_is_identity(self):
        """Test is_identity property."""
        assert self.projector.is_identity is True

    def test_source_to_geographic(self):
        """Test source to geographic transformation."""
        pixel = Pixel(x_px=35.0, y_px=-118.0)  # Use valid coordinate ranges
        geo = self.projector.source_to_geographic(pixel)

        assert geo.latitude_deg == pixel.x_px
        assert geo.longitude_deg == pixel.y_px

    def test_geographic_to_source(self):
        """Test geographic to source transformation."""
        geo = Geographic(latitude_deg=35.0, longitude_deg=-118.0)  # Use valid coordinate ranges
        pixel = self.projector.geographic_to_source(geo)

        assert pixel.x_px == geo.latitude_deg
        assert pixel.y_px == geo.longitude_deg


    def test_update_model(self):
        """Test update_model method (no-op for identity)."""
        # Should not raise any exceptions
        self.projector.update_model(any_param="value")

    def test_image_attributes(self):
        """Test image attribute methods."""
        # Test setting and getting source attributes
        self.projector.set_source_image_attributes(width=1000, height=800)
        attrs = self.projector.source_image_attributes
        assert attrs["width"] == 1000
        assert attrs["height"] == 800


    def test_roundtrip_transformation(self):
        """Test roundtrip transformation accuracy."""
        original_pixel = Pixel(x_px=35.123, y_px=-118.456)  # Use valid coordinates

        # Forward and inverse transformation
        geo = self.projector.source_to_geographic(original_pixel)
        result_pixel = self.projector.geographic_to_source(geo)

        # Should be exactly the same
        assert result_pixel.x_px == original_pixel.x_px
        assert result_pixel.y_px == original_pixel.y_px

    def test_multiple_roundtrip_precision(self):
        """Test multiple roundtrip transformations maintain precision."""
        original_pixel = Pixel(x_px=35.123, y_px=-118.456)  # Use valid coordinates
        current_pixel = original_pixel

        # Perform multiple roundtrips
        for _ in range(10):
            geo = self.projector.source_to_geographic(current_pixel)
            current_pixel = self.projector.geographic_to_source(geo)

        # Should maintain precision exactly
        assert current_pixel.x_px == original_pixel.x_px
        assert current_pixel.y_px == original_pixel.y_px

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with zero coordinates
        pixel = Pixel(x_px=0.0, y_px=0.0)
        geo = self.projector.source_to_geographic(pixel)
        assert geo.latitude_deg == 0.0
        assert geo.longitude_deg == 0.0

        # Test with negative coordinates (in valid range)
        pixel = Pixel(x_px=-45.0, y_px=-90.0)
        geo = self.projector.source_to_geographic(pixel)
        assert geo.latitude_deg == -45.0
        assert geo.longitude_deg == -90.0

        # Test with very small coordinates
        pixel = Pixel(x_px=1e-10, y_px=1e-10)
        geo = self.projector.source_to_geographic(pixel)
        assert abs(geo.latitude_deg - 1e-10) < 1e-15
        assert abs(geo.longitude_deg - 1e-10) < 1e-15
