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
#    File:    __init__.py
#    Author:  Marvin Smith
#    Date:    04/04/2026
#
"""
Terminus-Core Python

Base structures for Terminus Python APIs.
"""

# Python Standard Libraries
import logging

# Project Libraries
from tmns._version import __version__, __build_date__, __git_hash__

# Configure logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Export version information
__all__ = [
    '__version__',
    '__build_date__',
    '__git_hash__',
    'get_version_info',
]

def get_version_info():
    """Get comprehensive version information."""
    return {
        'version': __version__,
        'build_date': __build_date__,
        'git_hash': __git_hash__,
    }
