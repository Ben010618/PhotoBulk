"""
KameraPh Project Store (On-Disk Persistent Batch Storage)
---------------------------------------------------------
Replaces volatile in-memory dictionary with persistent on-disk project structure:
  <PROJECTS_DIR>/<project_id>/<photo_id>/
    - original.jpg   (full-resolution master input)
    - preview.jpg    (preview-sized image, ~1600px long edge)
    - alpha.png      (subject soft alpha matte, uint8 0-255)
    - face.json      (detected face bounding box & YuNet landmarks)
    - analysis.json  (sharpness, blink, roll/pitch/yaw, review flags)
    - settings.json  (active preset, sliders, backdrop choices)
    - render_master.jpg, render_8R.jpg, render_2x2.jpg (full-res exports)

Guarantees:
  1. Photos and adjustments survive server restarts.
  2. Heavy operations (face detection, neural matting) computed once and cached on disk.
  3. Interactive slider changes only execute cheap beauty/lighting steps on preview.jpg (<1s response).
  4. Full-resolution renders execute only during batch export jobs.
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import cv2
import numpy as np

from config import DATA_DIR, PROJECTS_DIR
from analyzer_engine import analyze_portrait
from pipeline import get_subject_mask, crop_8r_aspect, crop_2x2_id
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop, clean_original_backdrop
from beautification_presets import apply_beauty_preset_to_image, apply_studio_environment_lighting

logger = logging.getLogger("kameraph.project_store")

PREVIEW_LONG_EDGE = 1600


class ProjectStore:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or PROJECTS_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: str = "default_project") -> Path:
        p_dir = self.base_dir / project_id
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def get_photo_dir(self, project_id: str, photo_id: str) -> Path:
        photo_dir = self.get_project_dir(project_id) / photo_id
        photo_dir.mkdir(parents=True, exist_ok=True)
        return photo_dir

    def save_uploaded_photo(
        self,
        project_id: str,
        photo_id: str,
        filename: str,
        img_bgr: np.ndarray,
        studio_id: str = "default_studio",
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Saves original image, generates preview-size image, and initializes settings.json."""
        photo_dir = self.get_photo_dir(project_id, photo_id)
        h, w = img_bgr.shape[:2]

        # 1. Save original master
        orig_path = photo_dir / "original.jpg"
        cv2.imwrite(str(orig_path), img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        # 2. Save preview-size image (~1600px long edge)
        max_edge = max(w, h)
        scale = min(1.0, float(PREVIEW_LONG_EDGE) / float(max_edge))
        pw, ph = int(w * scale), int(h * scale)
        if scale < 1.0:
            preview_bgr = cv2.resize(img_bgr, (pw, ph), interpolation=cv2.INTER_AREA)
        else:
            preview_bgr = img_bgr.copy()
        preview_path = photo_dir / "preview.jpg"
        cv2.imwrite(str(preview_path), preview_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 88])

        # 3. Initialize settings.json
        settings = custom_settings or {
            "preset_id": "morena_radiant",
            "skin_smoothing": 0.65,
            "blemish_cut": 0.70,
            "dark_spot_whitening": 0.50,
            "shine_reduction": 0.35,
            "lip_color": "#d87093",
            "lip_intensity": 0.35,
            "glow_intensity": 0.35,
            "eye_catchlight": 0.35,
            "teeth_whitening": 0.45,
            "lighting_temp": "neutral_5500k",
            "studio_light_intensity": 0.20,
            "rim_light_boost": 0.20,
            "bg_replacement_enabled": True,
            "backdrop_type": "royal_navy"
        }
        self.save_json(photo_dir / "settings.json", settings)

        # 4. Save metadata summary
        meta = {
            "id": photo_id,
            "project_id": project_id,
            "studio_id": studio_id,
            "filename": filename,
            "width": w,
            "height": h,
            "preview_width": pw,
            "preview_height": ph,
            "scale": scale,
            "created_at": time.time(),
            "status": "staged"
        }
        self.save_json(photo_dir / "meta.json", meta)
        return meta

    def compute_and_cache_heavy_features(self, project_id: str, photo_id: str) -> Dict[str, Any]:
        """
        Computes heavy features once and caches them to disk:
          - Face landmarks and bounding box -> face.json
          - Quality analysis (sharpness, roll, pitch, blink) -> analysis.json
          - Subject alpha matte (neural segmentation) -> alpha.png
        """
        photo_dir = self.get_photo_dir(project_id, photo_id)
        face_path = photo_dir / "face.json"
        analysis_path = photo_dir / "analysis.json"
        alpha_path = photo_dir / "alpha.png"

        # Check if already cached
        if face_path.exists() and analysis_path.exists() and alpha_path.exists():
            face_info = self.load_json(face_path)
            analysis = self.load_json(analysis_path)
            return {"face_info": face_info, "analysis": analysis, "cached": True}

        orig_path = photo_dir / "original.jpg"
        if not orig_path.exists():
            raise FileNotFoundError(f"Original photo not found at {orig_path}")

        img_bgr = cv2.imread(str(orig_path))
        if img_bgr is None:
            raise ValueError(f"Could not read image at {orig_path}")

        # 1. AI Analysis & Face Geometry
        analysis = analyze_portrait(img_bgr)
        has_face = analysis.get("has_face", False)
        face_info = None
        if has_face and "face_box" in analysis:
            fb = analysis["face_box"]
            face_info = {
                "bbox": [fb["x"], fb["y"], fb["width"], fb["height"]]
            }
            if analysis.get("landmarks"):
                face_info.update(analysis["landmarks"])

        self.save_json(face_path, face_info)
        self.save_json(analysis_path, analysis)

        # 2. Subject Alpha Matte
        alpha_mask = get_subject_mask(img_bgr, face_info)
        cv2.imwrite(str(alpha_path), alpha_mask)

        # Update meta status
        meta_path = photo_dir / "meta.json"
        if meta_path.exists():
            meta = self.load_json(meta_path)
            meta["status"] = "analyzed"
            meta["has_face"] = has_face
            meta["review_needed"] = analysis.get("review_needed", False)
            self.save_json(meta_path, meta)

        return {"face_info": face_info, "analysis": analysis, "cached": False}

    def render_preview_fast(
        self,
        project_id: str,
        photo_id: str,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, int]:
        """
        Fast interactive preview render for slider adjustments:
          - Reads cached preview.jpg (~1600px)
          - Reads cached alpha.png (resized to preview scale)
          - Reads cached face.json (scaled to preview coordinates)
          - Executes only cheap beauty and lighting steps
          - Returns (preview_bgr, latency_ms) in under 1 second.
        """
        start_time = time.time()
        photo_dir = self.get_photo_dir(project_id, photo_id)

        preview_path = photo_dir / "preview.jpg"
        if not preview_path.exists():
            # Fallback to original
            preview_path = photo_dir / "original.jpg"

        preview_bgr = cv2.imread(str(preview_path))
        if preview_bgr is None:
            raise FileNotFoundError(f"Preview image not found at {preview_path}")

        ph, pw = preview_bgr.shape[:2]

        # Load or compute heavy features
        features = self.compute_and_cache_heavy_features(project_id, photo_id)
        face_info = features.get("face_info")
        analysis = features.get("analysis") or {}

        # Load alpha matte
        alpha_path = photo_dir / "alpha.png"
        if alpha_path.exists():
            alpha_full = cv2.imread(str(alpha_path), cv2.IMREAD_GRAYSCALE)
            if alpha_full is not None and (alpha_full.shape[0] != ph or alpha_full.shape[1] != pw):
                alpha_preview = cv2.resize(alpha_full, (pw, ph), interpolation=cv2.INTER_AREA)
            else:
                alpha_preview = alpha_full
        else:
            alpha_preview = np.full((ph, pw), 255, dtype=np.uint8)

        # Merge settings
        saved_settings = self.load_json(photo_dir / "settings.json") or {}
        active_settings = {**saved_settings, **(custom_settings or {})}

        # Scale face_info to preview coordinates
        meta = self.load_json(photo_dir / "meta.json") or {}
        orig_w = meta.get("width", pw)
        scale = float(pw) / float(max(orig_w, 1))

        preview_face_info = None
        if face_info and "bbox" in face_info:
            preview_face_info = {}
            for k, v in face_info.items():
                if isinstance(v, (list, tuple)):
                    preview_face_info[k] = [int(c * scale) for c in v]
                else:
                    preview_face_info[k] = v

        # 1. Backdrop Compositing
        bg_replacement = active_settings.get("bg_replacement_enabled", True)
        backdrop_mode = active_settings.get("backdrop_mode", "replace" if bg_replacement else "keep")
        backdrop_type = active_settings.get("backdrop_type", "classic_blue")

        if backdrop_mode == "clean":
            subject_isolated = clean_original_backdrop(preview_bgr, alpha_preview)
        elif backdrop_mode == "replace":
            backdrop = generate_studio_backdrop(pw, ph, backdrop_type=backdrop_type, face_info=preview_face_info)
            subject_isolated = composite_subject_onto_backdrop(preview_bgr, alpha_preview, backdrop)
        else:
            subject_isolated = preview_bgr.copy()

        # 2. Smart Auto-Corrections (Exposure & Tone)
        ev = float(analysis.get("auto_corrections", {}).get("exposure_compensation_ev", 0.0))
        if abs(ev) >= 0.10:
            factor = float(np.clip(2.0 ** (ev * 0.75), 0.70, 1.45))
            subject_isolated = np.clip(subject_isolated.astype(np.float32) * factor, 0.0, 255.0).astype(np.uint8)

        # 3. Fast Beauty & Lighting
        preset_id = active_settings.get("preset_id", "morena_radiant")
        if preview_face_info is not None:
            enhanced_preview = apply_beauty_preset_to_image(
                subject_isolated,
                face_info=preview_face_info,
                preset_id=preset_id,
                custom_adjustments=active_settings
            )
        else:
            # Skip facial steps, execute studio lighting
            lighting_temp = active_settings.get("lighting_temp", "neutral_5500k")
            studio_light_intensity = float(active_settings.get("studio_light_intensity", 0.20))
            rim_light_boost = float(active_settings.get("rim_light_boost", 0.20))
            lit_bgr = apply_studio_environment_lighting(
                subject_isolated.astype(np.float32),
                alpha_preview,
                lighting_temp=lighting_temp,
                studio_light_intensity=studio_light_intensity,
                rim_light_boost=rim_light_boost
            )
            enhanced_preview = np.clip(lit_bgr, 0, 255).astype(np.uint8)

        # Cache active settings
        if custom_settings:
            self.save_json(photo_dir / "settings.json", active_settings)

        latency_ms = max(1, int((time.time() - start_time) * 1000))
        return enhanced_preview, latency_ms

    def render_full_resolution(
        self,
        project_id: str,
        photo_id: str,
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Renders full master resolution and standard print crops for export job.
        Saves:
          - render_master.jpg
          - render_8R.jpg
          - render_2x2.jpg
        """
        start_time = time.time()
        photo_dir = self.get_photo_dir(project_id, photo_id)

        orig_path = photo_dir / "original.jpg"
        if not orig_path.exists():
            raise FileNotFoundError(f"Original photo not found at {orig_path}")

        img_bgr = cv2.imread(str(orig_path))
        if img_bgr is None:
            raise ValueError(f"Could not load image at {orig_path}")

        h, w = img_bgr.shape[:2]

        # Ensure features are computed and cached
        features = self.compute_and_cache_heavy_features(project_id, photo_id)
        face_info = features.get("face_info")
        analysis = features.get("analysis") or {}

        # Load alpha mask
        alpha_path = photo_dir / "alpha.png"
        alpha_mask = cv2.imread(str(alpha_path), cv2.IMREAD_GRAYSCALE)
        if alpha_mask is None or alpha_mask.shape[:2] != (h, w):
            alpha_mask = get_subject_mask(img_bgr, face_info)
            cv2.imwrite(str(alpha_path), alpha_mask)

        saved_settings = self.load_json(photo_dir / "settings.json") or {}
        active_settings = {**saved_settings, **(custom_settings or {})}

        # 1. Studio Backdrop Compositing
        bg_replacement = active_settings.get("bg_replacement_enabled", True)
        backdrop_mode = active_settings.get("backdrop_mode", "replace" if bg_replacement else "keep")
        backdrop_type = active_settings.get("backdrop_type", "classic_blue")

        if backdrop_mode == "clean":
            subject_isolated = clean_original_backdrop(img_bgr, alpha_mask)
        elif backdrop_mode == "replace":
            backdrop = generate_studio_backdrop(w, h, backdrop_type=backdrop_type, face_info=face_info)
            subject_isolated = composite_subject_onto_backdrop(img_bgr, alpha_mask, backdrop)
        else:
            subject_isolated = img_bgr.copy()

        # 2. Smart Auto-Corrections (Exposure & Tone)
        ev = float(analysis.get("auto_corrections", {}).get("exposure_compensation_ev", 0.0))
        if abs(ev) >= 0.10:
            factor = float(np.clip(2.0 ** (ev * 0.75), 0.70, 1.45))
            subject_isolated = np.clip(subject_isolated.astype(np.float32) * factor, 0.0, 255.0).astype(np.uint8)

        # 3. Beauty & Studio Lighting
        preset_id = active_settings.get("preset_id", "morena_radiant")
        if face_info is not None:
            enhanced_bgr = apply_beauty_preset_to_image(
                subject_isolated,
                face_info=face_info,
                preset_id=preset_id,
                custom_adjustments=active_settings
            )
        else:
            lighting_temp = active_settings.get("lighting_temp", "neutral_5500k")
            studio_light_intensity = float(active_settings.get("studio_light_intensity", 0.20))
            rim_light_boost = float(active_settings.get("rim_light_boost", 0.20))
            lit_bgr = apply_studio_environment_lighting(
                subject_isolated.astype(np.float32),
                alpha_mask,
                lighting_temp=lighting_temp,
                studio_light_intensity=studio_light_intensity,
                rim_light_boost=rim_light_boost
            )
            enhanced_bgr = np.clip(lit_bgr, 0, 255).astype(np.uint8)

        # 3. Print Crops
        crop_8r = crop_8r_aspect(enhanced_bgr)
        crop_2x2 = crop_2x2_id(enhanced_bgr, face_info)

        # 4. Save Renders with sRGB standard JPEG Quality 95
        master_path = photo_dir / "render_master.jpg"
        crop8r_path = photo_dir / "render_8R.jpg"
        crop2x2_path = photo_dir / "render_2x2.jpg"

        cv2.imwrite(str(master_path), enhanced_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cv2.imwrite(str(crop8r_path), crop_8r, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cv2.imwrite(str(crop2x2_path), crop_2x2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        latency_ms = max(1, int((time.time() - start_time) * 1000))
        return {
            "master_path": str(master_path),
            "crop_8r_path": str(crop8r_path),
            "crop_2x2_path": str(crop2x2_path),
            "latency_ms": latency_ms,
            "width": w,
            "height": h
        }

    def list_photos(self, project_id: str = "default_project") -> List[Dict[str, Any]]:
        """Lists all photo records for a given project from disk."""
        project_dir = self.get_project_dir(project_id)
        photos = []
        for p in project_dir.iterdir():
            if p.is_dir() and (p / "original.jpg").exists():
                meta = self.load_json(p / "meta.json") or {}
                settings = self.load_json(p / "settings.json") or {}
                analysis = self.load_json(p / "analysis.json") or {}
                photos.append({
                    "id": p.name,
                    "project_id": project_id,
                    "filename": meta.get("filename", f"{p.name}.jpg"),
                    "status": meta.get("status", "ready"),
                    "has_face": meta.get("has_face", False),
                    "review_needed": analysis.get("review_needed", False),
                    "review_reason": analysis.get("review_reason"),
                    "preview_url": f"/api/projects/{project_id}/photos/{p.name}/preview",
                    "master_url": f"/api/projects/{project_id}/photos/{p.name}/master",
                    "settings": settings,
                    "analysis": analysis
                })
        return photos

    @staticmethod
    def save_json(file_path: Path, data: Any):
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write json to {file_path}: {e}")

    @staticmethod
    def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
        if not file_path.exists():
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load json from {file_path}: {e}")
            return None


# Global singleton instance
project_store = ProjectStore()
