"""
KameraPh System Configuration & Feature Flags
--------------------------------------------
Centralized configuration module for application settings, AI models,
feature flags, and on-disk project storage paths.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load active environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

# =========================================================================
# FEATURE FLAGS
# =========================================================================
# STEP 0: Feature flag to disable payments, credits, and 402 checks for demo/local use
PAYMENTS_ENABLED = os.environ.get("PAYMENTS_ENABLED", "false").lower() in ("true", "1", "yes")

# AI / Neural Model Preferences
# u2net (0.44s on CPU) is default for laptop speed; birefnet-portrait is supported via env var
REMBG_MODEL = os.environ.get("REMBG_MODEL", "u2net")
BACKGROUND_REPLACEMENT_MODE = os.environ.get("BACKGROUND_REPLACEMENT_MODE", "replace")  # 'replace', 'clean', 'keep'

# =========================================================================
# STORAGE & PROJECT DIRECTORIES
# =========================================================================
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "local_data")).resolve()
PROJECTS_DIR = DATA_DIR / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

# Upload Limits
MAX_UPLOAD_SIZE = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 25)) * 1024 * 1024
MAX_PIXELS = int(os.environ.get("MAX_IMAGE_MEGAPIXELS", 50)) * 1_000_000
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/tiff"}

# Server Config
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "127.0.0.1")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("true", "1", "yes")
DEFAULT_JWT_SECRET = "kameraph_super_secret_jwt_key_philippines_2026"
JWT_SECRET = os.environ.get("JWT_SECRET", DEFAULT_JWT_SECRET)


def check_jwt_secret_security(debug_mode: bool = DEBUG, secret: str = JWT_SECRET) -> None:
    """Refuses to start when JWT_SECRET is the default value and DEBUG is false."""
    if not debug_mode and secret == DEFAULT_JWT_SECRET:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: Server refused to start. "
            "JWT_SECRET is set to the default insecure value while DEBUG is False. "
            "Please set a strong, unique JWT_SECRET environment variable in production."
        )


# Run startup check immediately if already running in production mode
if not DEBUG and JWT_SECRET == DEFAULT_JWT_SECRET:
    check_jwt_secret_security(DEBUG, JWT_SECRET)
