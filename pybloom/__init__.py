# pybloom/__init__.py

# Imports the main class from the bloom_filter module within this package
from .bloom_filter import BloomFilter

__version__ = "0.1.0"  # Initial version

# Controls what `from pybloom import *` imports
__all__ = ["BloomFilter"]
