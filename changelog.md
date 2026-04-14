# Changelog

All notable changes to terminus-core-python will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.6] - 2026-04-13

### Changed
* **Project name**: Renamed from `terminus-core-python` to `terminus_core`

## [0.1.5] - 2026-04-12

### Added
* **GCP.source** field (`str`, default `'manual'`) to track GCP origin (manual, auto, or algorithm ID)
* **GCP.metadata** field (`dict`, default empty) for arbitrary GCP metadata (confidence scores, timestamps, etc.)
* **Projector_Union** type alias (`Affine | TPS | RPC`) for cleaner type hints
* Tests for `GCP.source`, `GCP.metadata`, and backward compatibility

### Changed
* **GCP documentation**: Expanded docstrings with usage examples and serialization details
* **GCP serialization**: `to_dict()` and `from_dict()` now include `source` and `metadata` fields

## [0.1.4] - 2026-04-10

### Refactored
- **Transformation architecture**: Moved remap coordinate computation from centralized if/else branches to projector-specific implementations via new `compute_remap_coordinates` abstract method
- **Projector base class**: Added `compute_remap_coordinates(lon_mesh, lat_mesh, src_w, src_h)` abstract method for polymorphic coordinate remapping
- **Affine projector**: Implemented `compute_remap_coordinates` using inverse matrix multiplication
- **RPC projector**: Implemented `compute_remap_coordinates` using `geographic_to_source_batch` for efficient vectorized inverse transformation
- **TPS projector**: Implemented `compute_remap_coordinates` using sparse grid interpolation with `LinearNDInterpolator` for efficient warping
- **Identity projector**: Implemented `compute_remap_coordinates` using image bounds for linear mapping

### Added
- **RPC geographic_to_source_batch**: Added vectorized inverse transformation method for efficient batch coordinate conversion
- **RPC _compute_polynomial_batch**: Added vectorized polynomial computation method for batch coefficient evaluation
- **RPC unit tests**: Created comprehensive test suite (test_rpc.py) with 12 tests covering model updates, GCP fitting, transformations, batch operations, and polynomial computation

### Changed
- **transformation.py**: Updated `warp_image` function to use `projector.compute_remap_coordinates()` instead of type-specific conditional branches
- **TPS imports**: Moved `LinearNDInterpolator` import to top of file to comply with module rules

## [0.1.3] - 2026-04-10

### Tests
- Expanded unit test coverage to 77% across the codebase, adding tests for the projector factory, flat terrain source, and transformer. Fixed a UTM southern hemisphere zone bug uncovered during this work.

## [0.1.2] - 2026-04-10

### Added
- **Extent_Params**: Added NamedTuple for coordinate extent parameters (width, height, step_x, step_y) to reduce boilerplate in grid generation
- **Geographic.compute_extent_params**: Added static method to compute extent parameters for grid generation
- **UTM.compute_extent_params**: Added static method to compute extent parameters for grid generation
- **Warp_Extent**: Class to represent a geographic extent with min and max points
- **Warp_Extent.to_dict**: Added serialization method for Warp_Extent to dictionary
- **Warp_Extent.from_dict**: Added deserialization method for Warp_Extent from dictionary
- **Projector serialization**: Added serialize_model_data() method to Projector base class for GUI sidecar building
- **Geographic tests**: Added unit tests for compute_extent_params method


## [0.1.1] - 2026-04-09

### Added
- **Catalog Caching**: Added lazy loading with caching to terrain Catalog API for improved startup performance

## [0.1.0] - 2026-04-07

### Added
- **Future Annotations**: Added `from __future__ import annotations` to all coordinate classes for modern type hints
- **Modern Type Hints**: Updated Union types to use Python 3.10+ `|` syntax throughout codebase
- **Exception Chaining**: Added proper exception chaining with `raise ... from e` in error handling

### Fixed
- **Ruff Configuration**: Updated deprecated top-level settings to new lint section format

### Changed
- **Type Safety**: Enhanced type hint coverage and modern Python practices
- **Major Refactor**: Updated terrain and coord modules to use more concise naming.


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
