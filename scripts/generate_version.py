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
#    File:    generate_version.py
#    Author:  Marvin Smith
#    Date:    4/4/2026
#
"""
Build hook script - generates version info during pip install

This script runs during the build process and generates a _version.py file
containing version, build date, and git commit hash.
"""

# Python Standard Libraries
import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def get_git_hash() -> str:
    """Get the current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).parent.parent,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_build_date() -> str:
    """Get the current build date in ISO format."""
    return datetime.now(UTC).isoformat()


def generate_version_file():
    """Generate the _version.py file."""
    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    version = "0.0.1"  # Default

    if pyproject_path.exists():
        try:
            import tomllib
        except ImportError:
            # For Python < 3.11
            try:
                import tomli as tomllib
            except ImportError:
                logger.warning("tomllib/tomli not available, using default version")
                tomllib = None

        if tomllib:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                version = data.get("project", {}).get("version", version)

    git_hash = get_git_hash()
    build_date = get_build_date()

    version_content = f'''"""
Version information for Terminus-Core Python

This file is auto-generated during build - do not edit manually.
"""

__version__ = "{version}"
__build_date__ = "{build_date}"
__git_hash__ = "{git_hash}"


def get_version_info() -> dict:
    """Return version information as a dictionary."""
    return {{
        "version": __version__,
        "build_date": __build_date__,
        "git_hash": __git_hash__,
    }}
'''

    # Write to src/tmns/_version.py
    version_file_path = Path(__file__).parent.parent / "src" / "tmns" / "_version.py"
    version_file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(version_file_path, "w") as f:
        f.write(version_content)

    logger.info(f"Generated version file: {version_file_path}")
    logger.info(f"  Version: {version}")
    logger.info(f"  Build date: {build_date}")
    logger.info(f"  Git hash: {git_hash}")


if __name__ == "__main__":
    generate_version_file()
