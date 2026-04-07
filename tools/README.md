# Terminus-Core Tools

This directory contains utility tools for the Terminus-Core geospatial processing library.

## GCP Designer

The GCP (Ground Control Point) Designer tool generates realistic test data for validating geometric transformation algorithms in satellite imagery processing.

### Features

- **Multiple GCP Patterns**: Grid, distortion, linear, and random distributions
- **Realistic Scale**: Default 1920×1080 image size with configurable geographic coverage
- **Multiple Output Formats**: TXT, CSV, Python, and JSON
- **Test Point Generation**: Automatically generates validation points
- **Flexible Configuration**: Adjustable distortion, scaling, and density parameters

### Usage

```bash
# Generate 5x5 grid GCPs (default)
python tools/gcp_designer.py

# Generate distortion GCPs with 2° coverage
python tools/gcp_designer.py --pattern distortion --coverage 2.0 --output distortion_gcps.txt

# Generate 50 random GCPs with seed for reproducibility
python tools/gcp_designer.py --pattern random --n-points 50 --seed 123 --output random_gcps.csv

# Generate linear transformation test GCPs
python tools/gcp_designer.py --pattern linear --lat-scale 2.0 --lon-scale 3.0 --output linear_gcps.py

# Custom image size and grid
python tools/gcp_designer.py --pattern grid --image-width 4096 --image-height 2160 --grid-x 7 --grid-y 5
```

### Output Formats

- **TXT**: Simple comma-separated format with headers
- **CSV**: Standard CSV format for spreadsheet applications
- **Python**: Direct Python code with tmns.geo imports
- **JSON**: Structured JSON format for web applications

### Default Geographic Coverage

- **Location**: Los Angeles area (34-35°N, 119-118°W)
- **Coverage**: 1°×1° (adjustable with `--coverage`)
- **Image Size**: 1920×1080 pixels (configurable)

### GCP Patterns

#### Grid Pattern
Uniform grid distribution across the entire image. Ideal for testing interpolation accuracy and identity transformations.

#### Distortion Pattern  
Realistic satellite image distortion with:
- Exact corner points
- Slight edge distortions
- Complex interior distortions using sinusoidal patterns

#### Linear Pattern
Known linear transformations for testing solver accuracy:
- Configurable latitude and longitude scaling
- Perfectly predictable mapping
- Ideal for validating mathematical correctness

#### Random Pattern
Randomly distributed points for testing robustness:
- Configurable number of points
- Reproducible with seed option
- Good for stress testing algorithms

### Integration with Tests

The generated GCP data can be directly used in unit tests:

```python
from tools.gcp_designer import GCP_Designer

# Generate test data
designer = GCP_Designer()
gcps = designer.generate_grid_gcps(grid_x=5, grid_y=5)

# Use in TPS test
projector = TPS()
projector.update_model(control_points=gcps)
```

### Examples

#### Basic Grid Generation
```bash
python tools/gcp_designer.py --pattern grid --grid-x 5 --grid-y 5
```
Output: 25 GCPs in uniform 5×5 grid

#### Realistic Satellite Distortion
```bash
python tools/gcp_designer.py --pattern distortion --coverage 2.0 --distortion 0.002
```
Output: 22 GCPs with realistic distortion patterns

#### High-Resolution Grid
```bash
python tools/gcp_designer.py --pattern grid --image-width 4096 --image-height 2160 --grid-x 9 --grid-y 5
```
Output: 45 GCPs for 4K satellite imagery

### File Structure

```
tools/
├── gcp_designer.py          # Main GCP generation tool
├── README.md               # This documentation
└── generated/              # Generated GCP files (created during use)
    ├── identity_gcps.txt
    ├── distortion_gcps.csv
    └── test_points.json
```

### Requirements

- Python 3.8+
- tmns.geo module (from src/ directory)
- Standard libraries: argparse, math, random, pathlib, json, csv

### Contributing

When adding new tools to this directory:
1. Follow the existing code style and naming conventions
2. Include comprehensive documentation and examples
3. Add command-line interface for usability
4. Support multiple output formats when applicable
5. Include proper error handling and validation
