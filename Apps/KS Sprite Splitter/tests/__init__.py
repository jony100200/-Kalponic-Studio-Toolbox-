"""
Test suite for KS Sprite Splitter.

Comprehensive tests for all core components including backends,
pipeline processing, templates, and CLI functionality.
"""

import pytest
import numpy as np
import yaml
import tempfile
import os
from pathlib import Path

# Import the package
import ks_splitter
from ks_splitter import segment, matte, parts, mock_backends
from ks_splitter.pipeline import SpriteProcessor, PipelineRunner