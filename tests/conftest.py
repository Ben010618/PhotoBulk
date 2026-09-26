"""
pytest configuration and test fixtures for KameraPh.
Ensures:
- Tests strictly execute inside an isolated temporary DATA_DIR and never pollute local_data/.
- Generates real human portrait test fixtures dynamically from skimage.data.astronaut()
  so tests pass with zero skips without committing student PII (RA 10173 compliance).
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
import cv2
import skimage.data
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Create test-isolated temporary DATA_DIR
_TEST_TEMP_DIR = tempfile.TemporaryDirectory(prefix="kameraph_test_data_")
os.environ["DATA_DIR"] = _TEST_TEMP_DIR.name

# Pre-import and patch storage paths to guaranteed isolated temp directory
import config
config.DATA_DIR = Path(_TEST_TEMP_DIR.name).resolve()
config.PROJECTS_DIR = config.DATA_DIR / "projects"
config.PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

import export_engine
export_engine.DATA_DIR = config.DATA_DIR
export_engine.EXPORTS_DIR = config.DATA_DIR / "exports"
export_engine.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

import project_store
project_store.DATA_DIR = config.DATA_DIR
project_store.PROJECTS_DIR = config.PROJECTS_DIR
project_store.project_store.base_dir = config.PROJECTS_DIR


@pytest.fixture(scope="session", autouse=True)
def isolated_test_data_dir():
    """Session fixture managing isolated temporary DATA_DIR."""
    yield _TEST_TEMP_DIR.name
    # Cleanup temp directory
    try:
        _TEST_TEMP_DIR.cleanup()
    except Exception:
        pass


@pytest.fixture(scope="session")
def astronaut_portraits():
    """
    Generates real human face portrait fixtures at test time:
    - Standard astronaut (RGB converted to BGR, 512x512)
    - Darkened astronaut (simulating severe underexposure)
    - High-resolution 3000px upscaled astronaut (simulating high-DPI studio portrait)
    """
    standard_bgr = cv2.cvtColor(skimage.data.astronaut(), cv2.COLOR_RGB2BGR)
    darkened_bgr = cv2.convertScaleAbs(standard_bgr, alpha=0.45, beta=0)
    upscaled_3000 = cv2.resize(standard_bgr, (3000, 3000), interpolation=cv2.INTER_CUBIC)
    return {
        "standard": standard_bgr,
        "darkened": darkened_bgr,
        "upscaled_3000": upscaled_3000,
    }
