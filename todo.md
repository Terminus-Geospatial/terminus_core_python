# Terminus-Core Python TODO

## Project Overview
Terminus-Core Python is intended to be a base-level Python API for doing geospatial tasks. This project extracts core geospatial libraries from pointy-mcpointface for reuse across multiple projects.

## Current Migration Tasks (High Priority)

### ✅ Completed
- [x] Project analysis and dependency review
- [x] Create directory structure: src/tmns/geo/
- [x] Migrate coordinate.py to src/tmns/geo/coordinate.py
- [x] Migrate terrain.py to src/tmns/geo/terrain.py
- [x] Migrate datum.py to src/tmns/geo/datum.py
- [x] Migrate projector.py to src/tmns/geo/projector.py
- [x] Update terminus pyproject.toml with dependencies from pointy
- [x] Create generate_version.py script for terminus-core
- [x] Setup _version.py and __init__.py in terminus-core
- [x] Add terminus-core as dependency to pointy-mcpointface
- [x] Migrate unit tests from pointy to terminus-core
- [x] Migrate integration tests from pointy to terminus-core
- [x] Update all imports in pointy to use terminus-core
- [x] Apply proper IP headers and coding standards
- [x] Create pytest configuration and test infrastructure
- [x] Refactor coordinate module into smaller, focused files
- [x] Rename coordinate module to coord for brevity
- [x] Implement full imports throughout codebase
- [x] Configure pytest with coverage as opt-in only
- [x] Create comprehensive README with testing guide
- [x] Add enhanced logging with filename and line numbers
- [x] Fix EPSG Manager to return Coordinate_Type enum
- [x] Update all test imports for new coord module structure

### 🔄 In Progress
- [ ] Fix remaining terrain test failures (22 failed tests remaining)
- [ ] Fix missing Pixel import in terrain tests
- [ ] Update README to remove non-working marker examples
- [ ] Complete terrain module mock configuration fixes

### 📋 Next Steps
- [ ] Validate all tests pass in terminus-core
- [ ] Test package installation and imports

## Future Enhancement Ideas

### Core Geospatial Features
- [ ] **Coordinate Reference System (CRS) Management**
  - Enhanced CRS transformation utilities
  - Custom CRS definitions support
  - CRS validation and conversion tools

- [ ] **Geometric Operations**
  - Point-in-polygon testing
  - Buffer operations
  - Geometric intersection/union operations
  - Distance calculations (great circle, Euclidean, Manhattan)

- [ ] **Projection Systems**
  - Additional projection types (Lambert Conformal Conic, Albers Equal Area)
  - Custom projection parameters
  - Projection accuracy analysis

### Terrain and Elevation
- [ ] **Enhanced Elevation Services**
  - Support for additional elevation providers (NASA SRTM, USGS NED)
  - Elevation profile generation along paths
  - Viewshed analysis tools
  - Slope and aspect calculations

- [ ] **Terrain Analysis**
  - Contour generation
  - Watershed delineation
  - Terrain roughness metrics
  - Line-of-sight calculations

### Data Management
- [ ] **Geospatial Data I/O**
  - GeoJSON support
  - Shapefile support
  - KML/KMZ export/import
  - CSV coordinate data utilities

- [ ] **Caching and Performance**
  - Redis-based elevation caching
  - Coordinate transformation caching
  - Bulk operation optimizations
  - Memory-efficient data structures

### Image Georeferencing
- [ ] **Ground Control Points (GCP)**
  - GCP management and validation
  - Automatic GCP generation
  - GCP accuracy assessment
  - GCP-based transformation models

- [ ] **Image Registration**
  - Multi-image registration tools
  - Image-to-map registration
  - Cross-platform image support
  - Quality assessment metrics

### Advanced Sensor Models (from terminus_python)
- [ ] **Rational Polynomial Coefficients (RPC)**
  - RPC00B sensor model implementation
  - RPC coefficient parsing and validation
  - RPC-based image-to-ground transformations
  - Ground-to-image RPC projections
  - RPC accuracy assessment and refinement

- [ ] **Replacement Sensor Model (RSM)**
  - RSMIDA (Image Data) support
  - RSMPCA (Polynomial Coefficients) implementation
  - RSMPIA (Image Adjustments) support
  - Multi-section RSM handling
  - RSM coordinate transformations

- [ ] **Sensor Model Utilities**
  - Sensor model factory and registry
  - Model accuracy assessment tools
  - Model comparison and validation
  - Sensor model metadata management

### NITF (National Imagery Transmission Format) Support
- [ ] **NITF TRE (Textual Representation Elements)**
  - RSMAPA, RSMAPB, RSMDCA, RSMDCB TRE parsing
  - RSMECA, RSMECB (Elevation) TRE support
  - RSMGGA, RSMGIA (Grid) TRE implementation
  - RSMIDA, RSMPCA, RSMPIA TRE parsing
  - TRE field validation and extraction

- [ ] **NITF File Processing**
  - NITF header parsing
  - Image segment extraction
  - Metadata extraction from TREs
  - NITF file validation

### Web Map Services (WMS)
- [ ] **WMS Client Implementation**
  - WMS GetMap request construction
  - Bounding box calculations
  - Multi-layer WMS support
  - WMS tile loading and caching
  - Coordinate system transformations for WMS

- [ ] **Web Service Integration**
  - WMTS (Web Map Tile Service) support
  - WFS (Web Feature Service) client
  - Async web service operations
  - Service capability parsing

### Utilities and Tools
- [ ] **Coordinate Utilities**
  - Batch coordinate conversion
  - Coordinate format parsing (DMS, DD, UTM, MGRS)
  - Coordinate validation and cleaning
  - Time zone handling for geographic data

- [ ] **Metadata Management**
  - EXIF GPS data extraction
  - Geospatial metadata standards
  - Metadata validation and repair
  - Custom metadata schemas

### Integration and APIs
- [ ] **Web Service Integration**
  - REST API wrapper for core functions
  - Async/await support for network operations
  - Rate limiting and retry mechanisms
  - Authentication helpers for geospatial services

- [ ] **Third-party Service APIs**
  - Google Maps/Elevation API integration
  - Mapbox integration
  - OpenStreetMap data utilities
  - Commercial provider abstractions

### Testing and Documentation
- [ ] **Comprehensive Testing**
  - Unit tests for all coordinate transformations
  - Integration tests with real elevation data
  - Performance benchmarks
  - Accuracy validation against known datasets
  - Sensor model accuracy testing

- [ ] **Documentation and Examples**
  - API reference documentation
  - Tutorial notebooks
  - Use case examples
  - Migration guides from pointy-mcpointface
  - Sensor model documentation

### Packaging and Distribution
- [ ] **Package Management**
  - PyPI publishing setup
  - Version management strategy
  - Dependency management
  - Optional feature groups

- [ ] **Container Support**
  - Docker images for different use cases
  - Kubernetes deployment manifests
  - Cloud-ready configurations

## Technical Debt and Improvements

### Code Quality
- [ ] Add comprehensive type hints
- [ ] Implement error handling best practices
- [ ] Add logging configuration
- [ ] Performance profiling and optimization

### Architecture
- [ ] Plugin system for elevation providers
- [ ] Abstract interfaces for data sources
- [ ] Configuration management system
- [ ] Dependency injection improvements

## Dependencies to Extract from pointy-mcpointface

Based on analysis, these are the core dependencies needed for terminus-core:

### Essential Dependencies
- `numpy>=1.24.0` - Core numerical operations
- `pyproj>=3.6.0` - Coordinate reference system transformations
- `rasterio>=1.3.0` - Geospatial raster data I/O

### Optional Dependencies
- `matplotlib>=3.7.0` - Visualization and plotting
- `requests>=2.31.0` - HTTP client for web services
- `tqdm>=4.64.0` - Progress bars
- `python-dotenv>=1.0.0` - Environment configuration

### Additional Dependencies for Advanced Features
- `scipy>=1.10.0` - Scientific computing (for sensor models)
- `pillow>=10.0.0` - Image processing
- `affine>=2.4.0` - Affine transformations

### Development Dependencies
- `pytest>=7.0.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting and code analysis

## Migration Strategy

### Phase 2: Advanced Sensor Models
- [ ] RPC (Rational Polynomial Coefficients) implementation
- [ ] RSM (Replacement Sensor Model) support
- [ ] NITF TRE parsing capabilities
- [ ] Sensor model validation and testing

### Phase 3: Web Services and Data I/O
- [ ] WMS/WMTS client implementation
- [ ] Web service integration
- [ ] Geospatial data format support (GeoJSON, Shapefile)
- [ ] Network service utilities

### Phase 4: Integration and Optimization
- [ ] Integration testing and documentation
- [ ] Performance optimization
- [ ] Caching and memory management
- [ ] API design and interfaces

### Phase 5: Advanced Features
- [ ] Advanced geometric operations
- [ ] Custom projection support
- [ ] Plugin system implementation
- [ ] Cloud and container support

## Notes
- All migrated code should be updated to use `tmns` package namespace
- Remove pointy-specific dependencies and code
- Ensure all imports are properly updated
- Add comprehensive tests for all migrated functionality
- Update documentation to reflect new package structure
- Consider backward compatibility for existing pointy users
