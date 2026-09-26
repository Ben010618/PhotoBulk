"""
KameraPh Standardized ML Vision Pipeline (v3)
---------------------------------------------
Standardized entry point module conforming to Master Coding Directives:
  - Single type-hinted entry point: process_image(image_path: str, parameters: ProcessingParams) -> ProcessedImageResult
  - Strict Pydantic models for request/response payloads
  - Safe File I/O with pathlib.Path and directory creation
  - Zero Silent Failures with structured error reporting
"""

from pipeline import (
    process_image,
    ProcessingParams,
    ProcessedImageResult,
    process_complete_workflow,
    crop_8r_aspect,
    crop_2x2_id,
    get_subject_mask,
    detect_actual_engine,
    get_rembg_session
)

__all__ = [
    "process_image",
    "ProcessingParams",
    "ProcessedImageResult",
    "process_complete_workflow",
    "crop_8r_aspect",
    "crop_2x2_id",
    "get_subject_mask",
    "detect_actual_engine",
    "get_rembg_session"
]
