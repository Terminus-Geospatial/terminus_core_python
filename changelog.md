# Changelog

All notable changes to terminus-core-python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-04-06

### Added
- **RPC, Affine**: Added `solve_from_gcps()` to fit model coefficients from GCPs via least squares
- **Projector base**: Added `image_bounds()` and `geographic_bounds()` abstract methods; implemented in all projectors
- **TPS**: Replaced nearest-neighbor inverse with an iterative Newton solver (numerical Jacobian, sub-pixel accuracy)

### Fixed
- **TPS tests**: Fixed two failing tests (wrong expected values, degenerate GCPs)
- **Affine tests**: Fixed two failing tests (wrong matrix scale factors, invalid geographic output)
- **Identity**: Implemented missing `image_bounds()` and `geographic_bounds()` methods

### Changed
- **RPC, TPS, Affine tests**: Redesigned test suites with basic + GCP-based bidirectional roundtrip tests; tightened tolerances
- **TPS docs**: Added full mathematical documentation with references (Bookstein 1989, Duchon 1977, Wahba 1990, GDAL)
- **Affine docs**: Added matrix convention documentation and full method docstrings

## [0.0.1] - 2026-04-04

### Added
- Initial release of terminus-core-python library
- Core geospatial coordinate system support:
  - Geographic coordinates (latitude/longitude)
  - UTM coordinates (Universal Transverse Mercator)
  - UPS coordinates (Universal Polar Stereographic)
  - Web Mercator coordinates
  - ECEF coordinates (Earth-Centered Earth-Fixed)
  - Pixel coordinates
- Coordinate transformation utilities with Transformer class
- EPSG code management and validation
- Terrain elevation data access framework
- Geodetic datum definitions
- Projector API for abstract coordinate transformations
- Comprehensive test suite with 229 passing tests
- 73% code coverage across all modules
- Comprehensive README with usage examples and testing guide
