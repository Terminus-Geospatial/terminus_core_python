# Terminus Core Python

Base structures and utilities for Terminus Python APIs, providing geospatial coordinate systems, transformations, and terrain elevation data access.

## Features

- **Coordinate Systems**: Geographic, UTM, UPS, Web Mercator, ECEF, Pixel coordinates
- **Coordinate Transformations**: Seamless conversion between coordinate systems
- **EPSG Management**: Comprehensive EPSG code utilities and validation
- **Terrain Elevation**: Access to elevation data from multiple sources
- **Projector API**: Abstract coordinate transformation interface

## Installation

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Terminus-Geospatial/terminus-core-python.git
cd terminus-core-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Production Installation

```bash
pip install terminus-core-python
```

## Quick Start

```python
from tmns.geo import Geographic, UTM, Transformer

# Create geographic coordinate
geo = Geographic.create(40.7, -74.0, altitude_m=10.0)

# Transform to UTM
transformer = Transformer()
utm = transformer.geo_to_utm(geo)

print(f"Geographic: {geo}")
print(f"UTM: {utm}")
```

## Development

### Running Tests

#### Basic Test Commands

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest test/unit/geo/test_coordinate.py

# Run specific test class
pytest test/unit/geo/test_coordinate.py::Test_EPSG_Manager

# Run specific test method
pytest test/unit/geo/test_coordinate.py::Test_EPSG_Manager::test_get_coordinate_type
```

#### Test Categories

```bash
# Run all tests (current behavior - all tests are unmarked)
pytest

# Note: Markers like -m unit, -m integration, -m slow are not yet implemented
# All tests currently run by default since no markers are applied
```

#### Coverage Reports

```bash
# Generate terminal coverage report
pytest --cov=tmns

# Generate HTML coverage report (view in browser)
pytest --cov=tmns --cov-report=html
open htmlcov/index.html

# Generate XML coverage report (for CI systems)
pytest --cov=tmns --cov-report=xml

# Generate all coverage reports
pytest --cov=tmns --cov-report=term-missing --cov-report=html --cov-report=xml
```

#### Test Configuration

The project uses pytest configuration in `pyproject.toml` with the following defaults:

- `-ra`: Show summary for all tests except passes
- `--strict-markers`: Enforce marker registration
- `--strict-config`: Treat config warnings as errors
- `--verbose`: Detailed test output
- `--tb=short`: Compact traceback format

### Code Quality

#### Linting with Ruff

```bash
# Check for linting issues
ruff check

# Fix auto-fixable issues
ruff check --fix

# Check specific file
ruff check src/tmns/geo/coord/
```

#### Code Formatting with Black

```bash
# Check formatting
black --check src/ test/

# Format code
black src/ test/
```

### Project Structure

```
src/tmns/geo/
├── __init__.py          # Main geo package exports
├── coord/               # Coordinate systems module
│   ├── __init__.py
│   ├── types.py         # Coordinate type enums
│   ├── epsg.py          # EPSG code utilities
│   ├── geographic.py    # Geographic coordinates
│   ├── utm.py           # UTM coordinates
│   ├── ups.py           # UPS coordinates
│   ├── web_mercator.py  # Web Mercator coordinates
│   ├── ecef.py          # ECEF coordinates
│   ├── pixel.py         # Pixel coordinates
│   └── transformer.py   # Coordinate transformations
├── datum.py             # Geodetic datum definitions
├── projector.py         # Projection interface
└── terrain.py           # Elevation data access
```

## Usage Examples

### Coordinate Transformations

```python
from tmns.geo import Geographic, UTM, Web_Mercator, Transformer

# Create coordinates
geo = Geographic.create(40.7, -74.0)
utm = UTM.create(584482.35, 4505935.87, "EPSG:32618")
wm = Web_Mercator.create(-8238310.24, 4967049.90)

# Transform between coordinate systems
transformer = Transformer()

# Geographic to UTM
utm_from_geo = transformer.geo_to_utm(geo)

# UTM to Geographic
geo_from_utm = transformer.utm_to_geo(utm)

# Geographic to Web Mercator
wm_from_geo = transformer.geo_to_web_mercator(geo)

# Generic transformation (any type to any type)
any_coord = transformer.convert(geo, Coordinate_Type.UTM)
```

### EPSG Code Management

```python
from tmns.geo import EPSG_Manager

# Get coordinate type from EPSG code
coord_type = EPSG_Manager.get_coordinate_type(4326)  # Returns Coordinate_Type.GEOGRAPHIC

# Get description
description = EPSG_Manager.get_description(32618)  # Returns "WGS 84 / UTM zone 18N"

# Check if code is UTM zone
is_utm = EPSG_Manager.is_utm_zone(32618)  # Returns True

# Get UTM zone from coordinates
utm_zone = transformer.get_utm_zone(-74.0, 40.7)  # Returns "EPSG:32618"
```

### Terrain Elevation

```python
from tmns.geo import Geographic, elevation, elevation_point

# Get elevation at a point
geo = Geographic.create(40.7, -74.0)
elev = elevation(geo)  # Returns elevation in meters

# Get structured elevation point
elev_point = elevation_point(geo)  # Returns Elevation_Point object
print(f"Elevation: {elev_point.altitude_m}m")
print(f"Source: {elev_point.source}")
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Run linting (`ruff check --fix .`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## TODO

### Unit Tests

The following components need comprehensive unit test coverage:

#### High Priority
- [ ] **Terrain Source Module** (`src/tmns/geo/terrain/source/`)
  - [ ] `Base` abstract class methods
  - [ ] `GeoTIFF` implementation (coordinate transformations, interpolation)
  - [ ] `Flat` implementation (edge cases, coordinate validation)
  - [ ] Error handling and edge cases

- [ ] **Terrain Manager** (`src/tmns/geo/terrain/manager.py`)
  - [ ] Singleton pattern behavior
  - [ ] Caching functionality
  - [ ] Source priority management
  - [ ] Coordinate transformation handling

#### Medium Priority
- [ ] **Catalog** (`src/tmns/geo/terrain/catalog.py`)
  - [ ] Source discovery logic
  - [ ] Multi-source coordination
  - [ ] File system operations

#### Integration Tests
- [ ] Cross-module integration tests
- [ ] Performance benchmarks
- [ ] Real-world data validation
- [ ] Error recovery scenarios

### Test Data Requirements
- [ ] Sample GeoTIFF files for testing
- [ ] Known elevation data for validation
- [ ] Test coordinate sets covering different regions
- [ ] Mock data for edge cases

### Geographic Class Enhancements
- [ ] **Vincenty Formula Implementation** (`src/tmns/geo/coord/geographic.py`)
  - [ ] Vincenty formula implementation for accurate bearing calculations
  - [ ] Vincenty formula implementation for accurate distance calculations
  - [ ] Compare Vincenty vs Haversine accuracy for different use cases
  - [ ] Performance optimization for batch calculations

## Support

- **Issues**: [GitHub Issues](https://github.com/Terminus-Geospatial/terminus-core-python/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Terminus-Geospatial/terminus-core-python/discussions)
