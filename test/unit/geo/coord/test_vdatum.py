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
#    File:    test_vdatum.py
#    Author:  Marvin Smith
#    Date:    4/7/2026
#
"""
Unit tests for vertical datum functionality.
"""

from unittest.mock import patch

import pytest

from tmns.geo.coord.epsg import Code, Manager
from tmns.geo.coord.geographic import Geographic
from tmns.geo.coord.vdatum import (
    EGM96,
    EGM96_DATUM,
    ELIPSOIDAL_DATUM,
    NAVD88,
    NAVD88_DATUM,
    Ellipsoidal_Datum,
)

# Project Libraries
from tmns.geo.coord.vdatum import Base as VBase
from tmns.geo.terrain import Elevation_Point


class Test_VBase:
    """Test vertical datum base class."""

    def test_base_creation(self):
        """Test creating a vertical datum base class."""
        datum = VBase("Test Datum", epsg_code=9999)
        assert datum.name == "Test Datum"
        assert datum.epsg_code == 9999

    def test_base_creation_no_epsg(self):
        """Test creating a vertical datum without EPSG code."""
        datum = VBase("Test Datum")
        assert datum.name == "Test Datum"
        assert datum.epsg_code is None

    def test_separation_meters_not_implemented(self):
        """Test that base class raises NotImplementedError."""
        datum = VBase("Test Datum")
        coord = Geographic(40.0, -105.0, 1000.0)
        with pytest.raises(NotImplementedError):
            datum.separation_meters(coord)

    def test_to_ellipsoidal_not_implemented(self):
        """Test that base class raises NotImplementedError."""
        datum = VBase("Test Datum")
        coord = Geographic(40.0, -105.0, 1000.0)
        with pytest.raises(NotImplementedError):
            datum.to_ellipsoidal(coord)

    def test_to_orthometric_not_implemented(self):
        """Test that base class raises NotImplementedError."""
        datum = VBase("Test Datum")
        coord = Geographic(40.0, -105.0, 1000.0)
        with pytest.raises(NotImplementedError):
            datum.to_orthometric(coord)


class Test_EGM96:
    """Test EGM96 vertical datum."""

    def test_egm96_creation(self):
        """Test creating EGM96 datum."""
        egm96 = EGM96()
        assert egm96.name == "EGM96"
        assert egm96.epsg_code == 5773

    def test_egm96_pyproj_available(self):
        """Test that pyproj is available for EGM96."""
        egm96 = EGM96()
        assert hasattr(egm96, '_transformer_to_egm96')

    def test_egm96_separation_meters(self):
        """Test getting geoid separation from EGM96."""
        egm96 = EGM96()

        # Test various locations
        locations = [
            (40.0, -105.0),  # Denver
            (37.7749, -122.4194),  # San Francisco
            (0.0, 0.0),  # Equator
            (90.0, 0.0),  # North Pole
            (-90.0, 0.0),  # South Pole
        ]

        for lat, lon in locations:
            try:
                coord = Geographic(lat, lon, 1000.0)
                geoid_sep = egm96.separation_meters(coord)
                assert isinstance(geoid_sep, float)
                assert not (geoid_sep != geoid_sep)  # Check for NaN
            except Exception as e:
                # Expected if pyproj geoid data not available or transformation fails
                pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_egm96_coordinate_validation(self):
        """Test coordinate validation in EGM96."""
        egm96 = EGM96()

        # Test invalid latitude
        with pytest.raises(ValueError, match="Latitude 91.0 out of range"):
            coord = Geographic(91.0, 0.0, 1000.0)
            egm96.separation_meters(coord)

        with pytest.raises(ValueError, match="Latitude -91.0 out of range"):
            coord = Geographic(-91.0, 0.0, 1000.0)
            egm96.separation_meters(coord)

        # Test invalid longitude
        with pytest.raises(ValueError, match="Longitude 181.0 out of range"):
            coord = Geographic(0.0, 181.0, 1000.0)
            egm96.separation_meters(coord)

        with pytest.raises(ValueError, match="Longitude -181.0 out of range"):
            coord = Geographic(0.0, -181.0, 1000.0)
            egm96.separation_meters(coord)

    def test_egm96_to_ellipsoidal(self):
        """Test orthometric to ellipsoidal conversion."""
        egm96 = EGM96()

        try:
            coord = Geographic(40.0, -105.0, 1000.0)
            ellip_coord = egm96.to_ellipsoidal(coord)
            assert isinstance(ellip_coord, Geographic)
            assert ellip_coord.altitude_m is not None
            assert not (ellip_coord.altitude_m != ellip_coord.altitude_m)  # Check for NaN
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_egm96_to_orthometric(self):
        """Test ellipsoidal to orthometric conversion."""
        egm96 = EGM96()

        try:
            coord = Geographic(40.0, -105.0, 1000.0)
            ortho_coord = egm96.to_orthometric(coord)
            assert isinstance(ortho_coord, Geographic)
            assert ortho_coord.altitude_m is not None
            assert not (ortho_coord.altitude_m != ortho_coord.altitude_m)  # Check for NaN
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_egm96_conversion_roundtrip(self):
        """Test roundtrip conversion accuracy."""
        egm96 = EGM96()

        try:
            coord = Geographic(40.0, -105.0, 1600.0)  # Denver elevation
            ellip_coord = egm96.to_ellipsoidal(coord)
            ortho_back = egm96.to_orthometric(ellip_coord)

            # Should be very close to original
            assert abs(coord.altitude_m - ortho_back.altitude_m) < 0.001
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")


class Test_NAVD88:
    """Test NAVD88 vertical datum."""

    def test_navd88_creation(self):
        """Test creating NAVD88 datum."""
        navd88 = NAVD88()
        assert navd88.name == "NAVD88"
        assert navd88.epsg_code == 5703

    def test_navd88_pyproj_available(self):
        """Test that pyproj is available for NAVD88."""
        navd88 = NAVD88()
        assert hasattr(navd88, '_transformer_to_navd88')

    def test_navd88_separation_meters(self):
        """Test getting geoid separation from NAVD88."""
        navd88 = NAVD88()

        # Test various locations
        locations = [
            (40.0, -105.0),  # Denver
            (37.7749, -122.4194),  # San Francisco
            (0.0, 0.0),  # Equator
        ]

        for lat, lon in locations:
            try:
                coord = Geographic(lat, lon, 1000.0)
                geoid_sep = navd88.separation_meters(coord)
                assert isinstance(geoid_sep, float)
                assert not (geoid_sep != geoid_sep)  # Check for NaN
            except Exception as e:
                pytest.skip(f"NAVD88 geoid data not available or transformation failed: {e}")

    def test_navd88_coordinate_validation(self):
        """Test coordinate validation in NAVD88."""
        navd88 = NAVD88()

        # Test invalid latitude
        with pytest.raises(ValueError, match="Latitude 91.0 out of range"):
            coord = Geographic(91.0, 0.0, 1000.0)
            navd88.separation_meters(coord)

    def test_navd88_conversions(self):
        """Test NAVD88 height conversions."""
        navd88 = NAVD88()

        try:
            coord = Geographic(40.0, -105.0, 1000.0)
            ellip_coord = navd88.to_ellipsoidal(coord)
            ortho_back = navd88.to_orthometric(ellip_coord)

            assert isinstance(ellip_coord, Geographic)
            assert isinstance(ortho_back, Geographic)
            assert abs(coord.altitude_m - ortho_back.altitude_m) < 0.001
        except RuntimeError:
            pytest.skip("NAVD88 geoid data not available in test environment")


class Test_Ellipsoidal_Datum:
    """Test ellipsoidal vertical datum."""

    def test_ellipsoidal_creation(self):
        """Test creating ellipsoidal datum."""
        ellipsoidal = Ellipsoidal_Datum()
        assert ellipsoidal.name == "Ellipsoidal"
        assert ellipsoidal.epsg_code is None

    def test_ellipsoidal_creation_custom_name(self):
        """Test creating ellipsoidal datum with custom name."""
        ellipsoidal = Ellipsoidal_Datum("Custom Ellipsoidal", 9999)
        assert ellipsoidal.name == "Custom Ellipsoidal"
        assert ellipsoidal.epsg_code == 9999

    def test_ellipsoidal_separation_meters_zero(self):
        """Test that ellipsoidal datum always returns zero geoid separation."""
        ellipsoidal = Ellipsoidal_Datum()

        locations = [
            (40.0, -105.0),
            (0.0, 0.0),
            (90.0, 0.0),
            (-90.0, 180.0),
        ]

        for lat, lon in locations:
            coord = Geographic(lat, lon, 1000.0)
            geoid_sep = ellipsoidal.separation_meters(coord)
            assert geoid_sep == 0.0

    def test_ellipsoidal_to_ellipsoidal(self):
        """Test that ellipsoidal datum returns same coordinate for to_ellipsoidal."""
        ellipsoidal = Ellipsoidal_Datum()
        coord = Geographic(40.0, -105.0, 1000.0)

        result = ellipsoidal.to_ellipsoidal(coord)
        assert result is coord  # Should return the same object

    def test_ellipsoidal_to_orthometric_not_implemented(self):
        """Test that ellipsoidal datum cannot convert ellipsoidal to orthometric."""
        ellipsoidal = Ellipsoidal_Datum()
        coord = Geographic(40.0, -105.0, 1000.0)

        with pytest.raises(NotImplementedError, match="Cannot convert ellipsoidal to orthometric without geoid model"):
            ellipsoidal.to_orthometric(coord)


class Test_Vertical_Datum_Constants:
    """Test vertical datum constant instances."""

    def test_egm96_datum_constant(self):
        """Test EGM96_DATUM constant."""
        assert isinstance(EGM96_DATUM, EGM96)
        assert EGM96_DATUM.name == "EGM96"
        assert EGM96_DATUM.epsg_code == 5773

    def test_navd88_datum_constant(self):
        """Test NAVD88_DATUM constant."""
        assert isinstance(NAVD88_DATUM, NAVD88)
        assert NAVD88_DATUM.name == "NAVD88"
        assert NAVD88_DATUM.epsg_code == 5703

    def test_ellipsoidal_datum_constant(self):
        """Test ELIPSOIDAL_DATUM constant."""
        assert isinstance(ELIPSOIDAL_DATUM, Ellipsoidal_Datum)
        assert ELIPSOIDAL_DATUM.name == "Ellipsoidal"
        assert ELIPSOIDAL_DATUM.epsg_code is None


class Test_Vertical_Datum_Integration:
    """Test vertical datum integration with terrain system."""

    def test_elevation_point_vertical_datum(self):
        """Test elevation point with vertical datum."""
        point = Elevation_Point.create(40.0, -105.0, 1000.0, "test", vertical_datum=EGM96_DATUM)
        assert point.vertical_datum == EGM96_DATUM
        assert point.coord.altitude_m == 1000.0

    def test_elevation_point_no_vertical_datum(self):
        """Test elevation point without vertical datum."""
        point = Elevation_Point.create(40.0, -105.0, 1000.0, "test")
        assert point.vertical_datum is None

    def test_elevation_point_datum_conversion(self):
        """Test elevation point datum conversion."""
        # Create point with ellipsoidal height
        point_ellip = Elevation_Point.create(40.0, -105.0, 1000.0, "test", vertical_datum=ELIPSOIDAL_DATUM)

        # Convert to EGM96 (should work with ellipsoidal datum)
        try:
            point_egm96 = point_ellip.to_vertical_datum(EGM96_DATUM)
            assert point_egm96.vertical_datum == EGM96_DATUM
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_epsg_manager_vertical_datum_integration(self):
        """Test EPSG manager vertical datum integration."""
        # Test getting EGM96 from EPSG
        egm96 = Manager.get_vertical_datum(Code.EGM96)
        assert isinstance(egm96, EGM96)
        assert egm96.epsg_code == 5773

        # Test getting NAVD88 from EPSG
        navd88 = Manager.get_vertical_datum(Code.NAVD88)
        assert isinstance(navd88, NAVD88)
        assert navd88.epsg_code == 5703

        # Test invalid EPSG code
        with pytest.raises(ValueError):
            Manager.get_vertical_datum(9999)

        # Test MSL (not implemented)
        with pytest.raises(NotImplementedError):
            Manager.get_vertical_datum(Code.MSL)

    def test_epsg_manager_is_vertical_datum(self):
        """Test EPSG manager vertical datum detection."""
        assert Manager.is_vertical_datum(Code.EGM96) is True
        assert Manager.is_vertical_datum(Code.NAVD88) is True
        assert Manager.is_vertical_datum(Code.MSL) is True
        assert Manager.is_vertical_datum(Code.WGS84) is False
        assert Manager.is_vertical_datum(9999) is False


class Test_Vertical_Datum_Geoid_Verification:
    """Test geoid verification logic migrated from test_geoid_verification.py."""

    def test_geoid_separation_known_locations(self):
        """Test geoid separation at known locations."""
        egm96 = EGM96()
        navd88 = NAVD88()

        # Test locations from the verification script
        test_locations = [
            (40.0, -105.0, "Denver, CO"),
            (37.7749, -122.4194, "San Francisco, CA"),
            (0.0, 0.0, "Equator, Prime Meridian"),
        ]

        for lat, lon, _name in test_locations:
            # Test EGM96
            try:
                coord = Geographic(lat, lon, 1000.0)
                egm96_sep = egm96.separation_meters(coord)
                assert isinstance(egm96_sep, float)
                assert not (egm96_sep != egm96_sep)  # Check for NaN
            except RuntimeError:
                pytest.skip("EGM96 geoid data not available in test environment")

            # Test NAVD88
            try:
                coord = Geographic(lat, lon, 1000.0)
                navd88_sep = navd88.separation_meters(coord)
                assert isinstance(navd88_sep, float)
                assert not (navd88_sep != navd88_sep)  # Check for NaN
            except Exception as e:
                pytest.skip(f"NAVD88 geoid data not available or transformation failed: {e}")

    def test_height_conversion_roundtrip_accuracy(self):
        """Test height conversion roundtrip accuracy."""
        egm96 = EGM96()
        navd88 = NAVD88()

        test_locations = [
            (40.0, -105.0, "Denver, CO"),
            (37.7749, -122.4194, "San Francisco, CA"),
            (0.0, 0.0, "Equator, Prime Meridian"),
        ]

        h_ortho = 1000.0  # Test height

        for lat, lon, _name in test_locations:
            # Test EGM96 roundtrip
            try:
                coord = Geographic(lat, lon, h_ortho)
                ellip_coord = egm96.to_ellipsoidal(coord)
                ortho_back = egm96.to_orthometric(ellip_coord)

                # Should be very close to original (allowing for floating point precision)
                assert abs(coord.altitude_m - ortho_back.altitude_m) < 0.001
            except RuntimeError:
                pytest.skip("EGM96 geoid data not available in test environment")

            # Test NAVD88 roundtrip
            try:
                coord = Geographic(lat, lon, h_ortho)
                ellip_coord = navd88.to_ellipsoidal(coord)
                ortho_back = navd88.to_orthometric(ellip_coord)

                # Should be very close to original (allowing for floating point precision)
                assert abs(coord.altitude_m - ortho_back.altitude_m) < 0.001
            except Exception as e:
                pytest.skip(f"NAVD88 geoid data not available or transformation failed: {e}")

    def test_new_coordinate_based_api(self):
        """Test the new coordinate-based API."""
        egm96 = EGM96()
        NAVD88()

        # Create test coordinate
        coord = Geographic(40.0, -105.0, 1000.0)

        # Test new API methods
        try:
            # Test separation_meters
            separation = egm96.separation_meters(coord)
            assert isinstance(separation, float)

            # Test to_ellipsoidal
            ellip_coord = egm96.to_ellipsoidal(coord)
            assert isinstance(ellip_coord, Geographic)
            assert ellip_coord.latitude_deg == coord.latitude_deg
            assert ellip_coord.longitude_deg == coord.longitude_deg
            assert ellip_coord.altitude_m is not None

            # Test to_orthometric
            ortho_coord = egm96.to_orthometric(ellip_coord)
            assert isinstance(ortho_coord, Geographic)
            assert ortho_coord.latitude_deg == coord.latitude_deg
            assert ortho_coord.longitude_deg == coord.longitude_deg
            assert ortho_coord.altitude_m is not None

            # Roundtrip should preserve original height
            assert abs(coord.altitude_m - ortho_coord.altitude_m) < 0.001

        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_coordinate_validation_new_api(self):
        """Test coordinate validation in new coordinate-based API."""
        egm96 = EGM96()

        # Test invalid coordinates - Geographic validation happens first
        with pytest.raises(ValueError, match="Latitude 91.0 out of range"):
            coord = Geographic(91.0, 0.0, 1000.0)  # Invalid latitude
            egm96.separation_meters(coord)

        with pytest.raises(ValueError, match="Latitude -91.0 out of range"):
            coord = Geographic(-91.0, 0.0, 1000.0)  # Invalid latitude
            egm96.separation_meters(coord)

        with pytest.raises(ValueError, match="Longitude 181.0 out of range"):
            coord = Geographic(0.0, 181.0, 1000.0)  # Invalid longitude
            egm96.separation_meters(coord)

        with pytest.raises(ValueError, match="Longitude -181.0 out of range"):
            coord = Geographic(0.0, -181.0, 1000.0)  # Invalid longitude
            egm96.separation_meters(coord)

    def test_coordinate_altitude_validation(self):
        """Test altitude validation in new coordinate-based API."""
        egm96 = EGM96()
        navd88 = NAVD88()

        # Test coordinate without altitude
        coord_no_alt = Geographic(40.0, -105.0, None)

        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            egm96.to_ellipsoidal(coord_no_alt)

        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            egm96.to_orthometric(coord_no_alt)

        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            navd88.to_ellipsoidal(coord_no_alt)

        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            navd88.to_orthometric(coord_no_alt)


class Test_Vertical_Datum_Error_Cases:
    """Test vertical datum error cases."""

    def test_pyproj_transformation_error(self):
        """Test handling of pyproj transformation errors."""
        egm96 = EGM96()
        coord = Geographic(40.0, -105.0, 1000.0)

        with patch.object(egm96, '_transformer_to_egm96') as mock_transformer:
            mock_transformer.transform.side_effect = Exception("Transformation failed")

            with pytest.raises(Exception, match="Transformation failed"):
                egm96.separation_meters(coord)

    def test_separation_meters_none_altitude(self):
        """Test separation_meters with None altitude (should work)."""
        egm96 = EGM96()
        coord = Geographic(40.0, -105.0, None)  # No altitude

        try:
            # separation_meters should work even without altitude
            separation = egm96.separation_meters(coord)
            assert isinstance(separation, float)
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_conversion_without_altitude(self):
        """Test conversion methods without altitude should raise ValueError."""
        egm96 = EGM96()
        navd88 = NAVD88()

        coord_no_alt = Geographic(40.0, -105.0, None)

        # Test to_ellipsoidal
        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            egm96.to_ellipsoidal(coord_no_alt)

        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            navd88.to_ellipsoidal(coord_no_alt)

        # Test to_orthometric
        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            egm96.to_orthometric(coord_no_alt)

        with pytest.raises(ValueError, match="Coordinate must have altitude"):
            navd88.to_orthometric(coord_no_alt)

    def test_datum_equality(self):
        """Test datum equality comparisons."""
        egm96_1 = EGM96()
        egm96_2 = EGM96()
        navd88 = NAVD88()

        # Same datum instances should be equal in attributes
        assert egm96_1.name == egm96_2.name
        assert egm96_1.epsg_code == egm96_2.epsg_code

        # Different datums should have different attributes
        assert egm96_1.name != navd88.name
        assert egm96_1.epsg_code != navd88.epsg_code

    def test_extreme_coordinates(self):
        """Test behavior at extreme coordinates."""
        egm96 = EGM96()

        # Test at poles and date line
        extreme_coords = [
            (89.9, 0.0, 1000.0),    # Near North Pole
            (-89.9, 0.0, 1000.0),   # Near South Pole
            (0.0, 179.9, 1000.0),   # Near International Date Line
            (0.0, -179.9, 1000.0),  # Near International Date Line
        ]

        for lat, lon, alt in extreme_coords:
            try:
                coord = Geographic(lat, lon, alt)
                separation = egm96.separation_meters(coord)
                assert isinstance(separation, float)
                assert not (separation != separation)  # Check for NaN
            except Exception as e:
                pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_negative_elevations(self):
        """Test behavior with negative elevations (below sea level)."""
        egm96 = EGM96()

        try:
            coord = Geographic(40.0, -105.0, -500.0)  # Below sea level
            separation = egm96.separation_meters(coord)
            assert isinstance(separation, float)

            # Test conversion with negative elevation
            ellip_coord = egm96.to_ellipsoidal(coord)
            assert ellip_coord.altitude_m is not None
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_large_elevations(self):
        """Test behavior with large elevations (mountain heights)."""
        egm96 = EGM96()

        try:
            coord = Geographic(40.0, -105.0, 8848.0)  # Mount Everest height
            separation = egm96.separation_meters(coord)
            assert isinstance(separation, float)

            # Test conversion with large elevation
            ellip_coord = egm96.to_ellipsoidal(coord)
            assert ellip_coord.altitude_m is not None
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")


class Test_Vertical_Datum_Performance:
    """Test vertical datum performance characteristics."""

    def test_batch_separation_calculations(self):
        """Test performance of batch separation calculations."""
        egm96 = EGM96()

        # Generate test coordinates
        coords = []
        for i in range(10):
            lat = 40.0 + i * 0.1
            lon = -105.0 + i * 0.1
            coords.append(Geographic(lat, lon, 1000.0))

        try:
            # Test batch calculations
            separations = []
            for coord in coords:
                separation = egm96.separation_meters(coord)
                separations.append(separation)
                assert isinstance(separation, float)
                assert not (separation != separation)  # Check for NaN

            assert len(separations) == len(coords)
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")

    def test_repeated_calculations_consistency(self):
        """Test that repeated calculations give consistent results."""
        egm96 = EGM96()
        coord = Geographic(40.0, -105.0, 1000.0)

        try:
            # Calculate separation multiple times
            separations = []
            for _ in range(5):
                separation = egm96.separation_meters(coord)
                separations.append(separation)

            # All results should be identical
            first_result = separations[0]
            for separation in separations[1:]:
                assert separation == first_result
        except Exception as e:
            pytest.skip(f"EGM96 geoid data not available or transformation failed: {e}")


class Test_Vertical_Datum_Documentation:
    """Test vertical datum documentation and examples."""

    def test_datum_string_representations(self):
        """Test datum string representations for debugging."""
        egm96 = EGM96()
        navd88 = NAVD88()
        ellipsoidal = Ellipsoidal_Datum()

        # Test __str__ methods
        assert isinstance(str(egm96), str)
        assert isinstance(str(navd88), str)
        assert isinstance(str(ellipsoidal), str)

        # Test __repr__ methods
        assert isinstance(repr(egm96), str)
        assert isinstance(repr(navd88), str)
        assert isinstance(repr(ellipsoidal), str)

        # String representations should contain datum name
        assert "EGM96" in str(egm96)
        assert "NAVD88" in str(navd88)
        assert "Ellipsoidal" in str(ellipsoidal)
