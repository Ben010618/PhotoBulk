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
import re
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from fastapi import HTTPException
import cv2
import numpy as np

import config
from config import PROJECTS_DIR
from analyzer_engine import analyze_portrait
from pipeline import get_subject_mask, crop_8r_aspect, crop_2x2_id
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop, clean_original_backdrop
from beautification_presets import apply_beauty_preset_to_image, cleanup_flyaway_hair_alpha, PRESET_ALIASES

logger = logging.getLogger("kameraph.project_store")

PREVIEW_LONG_EDGE = 1600

ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def validate_id(identifier: str, name: str = "id") -> str:
    """Validates that project_id or photo_id strictly matches ^[A-Za-z0-9_-]{1,64}$ with no path traversal."""
    if not identifier or not isinstance(identifier, str) or not ID_REGEX.match(identifier):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {name} '{identifier}': must strictly match pattern ^[A-Za-z0-9_-]{{1,64}}$ with no path traversal."
        )
    return identifier


class ProjectStore:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or PROJECTS_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_id: str = "default_project") -> Path:
        validate_id(project_id, "project_id")
        p_dir = (self.base_dir / project_id).resolve()
        if not p_dir.is_relative_to(self.base_dir):
            raise HTTPException(
                status_code=400,
                detail=f"Security violation: project_id '{project_id}' attempts directory traversal outside PROJECTS_DIR."
            )
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def get_photo_dir(self, project_id: str, photo_id: str) -> Path:
        validate_id(photo_id, "photo_id")
        p_dir = self.get_project_dir(project_id)
        photo_dir = (p_dir / photo_id).resolve()
        if not photo_dir.is_relative_to(self.base_dir):
            raise HTTPException(
                status_code=400,
                detail=f"Security violation: photo_id '{photo_id}' attempts directory traversal outside PROJECTS_DIR."
            )
        photo_dir.mkdir(parents=True, exist_ok=True)
        return photo_dir

    def find_photo_dir(self, photo_id: str) -> Optional[Path]:
        """Finds photo directory across projects on disk without requiring in-memory cache."""
        try:
            validate_id(photo_id, "photo_id")
        except HTTPException:
            return None
        default_dir = (self.base_dir / "default_project" / photo_id).resolve()
        if default_dir.exists() and (default_dir / "original.jpg").exists():
            return default_dir
        if not self.base_dir.exists():
            return None
        for p_dir in self.base_dir.iterdir():
            if p_dir.is_dir() and not p_dir.name.startswith("."):
                candidate = (p_dir / photo_id).resolve()
                if candidate.exists() and (candidate / "original.jpg").exists():
                    return candidate
        return None

    def save_uploaded_photo(
        self,
        project_id: str,
        photo_id: str,
        filename: str,
        img_bgr: Optional[np.ndarray] = None,
        raw_bytes: Optional[bytes] = None,
        studio_id: str = "default_studio",
        custom_settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Saves original uploaded bytes (preserving EXIF and ICC metadata),
        creates a separate working JPEG if needed, generates a preview-size image,
        and initializes settings.json. Fast operation with zero heavy ML inference.
        """
        self.get_or_create_project(project_id, studio_id=studio_id)
        photo_dir = self.get_photo_dir(project_id, photo_id)

        # 1. Determine original extension and save raw uploaded bytes directly
        ext = Path(filename).suffix.lower() if filename else ".jpg"
        if not ext:
            ext = ".jpg"

        orig_ext_path = photo_dir / f"original{ext}"
        working_jpg_path = photo_dir / "original.jpg"

        if raw_bytes is not None:
            # Write exact raw uploaded bytes preserving 100% of EXIF, ICC, and original sensor data
            with open(orig_ext_path, "wb") as f:
                f.write(raw_bytes)
            
            # If original is JPEG, working JPEG is identical to raw bytes
            if ext in [".jpg", ".jpeg"]:
                if orig_ext_path != working_jpg_path:
                    with open(working_jpg_path, "wb") as f:
                        f.write(raw_bytes)
            
            # Decode for preview generation if img_bgr not provided
            if img_bgr is None:
                img_bgr = cv2.imdecode(np.frombuffer(raw_bytes, np.uint8), cv2.IMREAD_COLOR)
                if img_bgr is None:
                    raise ValueError(f"Failed to decode uploaded image: {filename}")
        else:
            # Fallback if only numpy array provided
            if img_bgr is None:
                raise ValueError("Either raw_bytes or img_bgr must be provided to save_uploaded_photo")
            cv2.imwrite(str(orig_ext_path), img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            if orig_ext_path != working_jpg_path:
                cv2.imwrite(str(working_jpg_path), img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        # If non-JPEG format (e.g. PNG, WebP), ensure working JPEG is written for downstream ML
        if not working_jpg_path.exists():
            cv2.imwrite(str(working_jpg_path), img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        h, w = img_bgr.shape[:2]

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

        # 3. Initialize settings.json with valid default IDs
        settings = custom_settings or {
            "preset_id": "natural",
            "skin_smoothing": 0.50,
            "blemish_cut": 0.60,
            "dark_spot_whitening": 0.40,
            "shine_reduction": 0.30,
            "lip_color": "#d87093",
            "lip_intensity": 0.0,
            "glow_intensity": 0.20,
            "eye_catchlight": 0.20,
            "teeth_whitening": 0.40,
            "lighting_temp": "neutral_5500k",
            "studio_light_intensity": 0.20,
            "rim_light_boost": 0.18,
            "bg_replacement_enabled": True,
            "backdrop_type": "classic_blue",
            "color_profile": "clean_commercial",
            "color_warmth": 0.0,
            "color_contrast": 0.0,
            "color_vibrance": 0.0,
            "has_user_override": False
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
            "status": "staged",
            "has_user_override": False
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
        masks_path = photo_dir / "masks.npz"

        # The subject matte is tied to the segmentation model that produced it; switching
        # REMBG_MODEL (e.g. u2net -> isnet-general-use, which keeps mortarboards) recomputes it.
        alpha_model_path = photo_dir / "alpha_model.txt"
        current_model = getattr(config, "REMBG_MODEL", "u2net")
        alpha_fresh = (
            alpha_path.exists()
            and alpha_model_path.exists()
            and alpha_model_path.read_text(encoding="utf-8").strip() == current_model
        )
        analysis_cached = face_path.exists() and analysis_path.exists()

        if analysis_cached and alpha_fresh:
            face_info = self.load_json(face_path)
            analysis = self.load_json(analysis_path)
            # Photos without a face never get masks.npz, so it must not be required for a cache hit
            if face_info is None or masks_path.exists():
                return {"face_info": face_info, "analysis": analysis, "cached": True}

        orig_path = photo_dir / "original.jpg"
        if not orig_path.exists():
            raise FileNotFoundError(f"Original photo not found at {orig_path}")

        img_bgr = cv2.imread(str(orig_path))
        if img_bgr is None:
            raise ValueError(f"Could not read image at {orig_path}")

        # 1. AI Analysis & Face Geometry
        if analysis_cached:
            face_info = self.load_json(face_path)
            analysis = self.load_json(analysis_path) or {}
            has_face = face_info is not None
        else:
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
        if alpha_fresh:
            alpha_mask = cv2.imread(str(alpha_path), cv2.IMREAD_GRAYSCALE)
        else:
            alpha_mask = get_subject_mask(img_bgr, face_info)
            cv2.imwrite(str(alpha_path), alpha_mask)
            alpha_model_path.write_text(current_model, encoding="utf-8")
            # The edge-decontaminated preview was derived from the old matte
            (photo_dir / "preview_clean.jpg").unlink(missing_ok=True)

        # 3. Face Parsing Masks (cached to disk for instant interactive slider response)
        masks_path = photo_dir / "masks.npz"
        if not masks_path.exists() and face_info is not None:
            try:
                from face_parsing import get_face_parsing_masks
                masks = get_face_parsing_masks(img_bgr, face_info)
                np.savez_compressed(str(masks_path), **masks)
            except Exception as e:
                logger.warning(f"Notice precomputing masks for {photo_id}: {e}")

        # 4. Precompute edge-decontaminated preview for sub-second compositing
        clean_p = photo_dir / "preview_clean.jpg"
        preview_p = photo_dir / "preview.jpg"
        if not clean_p.exists() and preview_p.exists():
            try:
                p_bgr = cv2.imread(str(preview_p))
                if p_bgr is not None:
                    p_alpha = cv2.resize(alpha_mask, (p_bgr.shape[1], p_bgr.shape[0]))
                    from background_engine import decontaminate_edges
                    clean_bgr = decontaminate_edges(p_bgr, p_alpha)
                    cv2.imwrite(str(clean_p), clean_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            except Exception as e:
                logger.warning(f"Notice precomputing decontaminated preview for {photo_id}: {e}")

        # Update meta status
        meta_path = photo_dir / "meta.json"
        if meta_path.exists():
            meta = self.load_json(meta_path)
            meta["status"] = "analyzed"
            meta["has_face"] = has_face
            meta["review_needed"] = analysis.get("review_needed", False)
            self.save_json(meta_path, meta)

        return {"face_info": face_info, "analysis": analysis, "cached": False}

    @staticmethod
    def _apply_auto_corrections(img_bgr: np.ndarray, analysis: Dict[str, Any]) -> np.ndarray:
        """Per-photo exposure and white-balance harmonization from the upload analysis."""
        out = img_bgr
        ev = float(analysis.get("auto_corrections", {}).get("exposure_compensation_ev", 0.0))
        if abs(ev) >= 0.10:
            factor = float(np.clip(2.0 ** ev, 0.50, 2.80))
            out = np.clip(out.astype(np.float32) * factor, 0.0, 255.0).astype(np.uint8)

        wb_cast = analysis.get("white_balance_cast") or {}
        delta_b = float(wb_cast.get("delta_b", 0.0))
        if abs(delta_b) >= 2.0:
            lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB).astype(np.float32)
            b_shift = float(np.clip(-delta_b * 0.75, -25.0, 25.0))
            lab[:, :, 2] = np.clip(lab[:, :, 2] + b_shift, 0.0, 255.0)
            out = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
        return out

    @staticmethod
    def _load_masks(masks_path: Path, h: int, w: int, photo_id: str) -> Optional[Dict[str, np.ndarray]]:
        if not masks_path.exists():
            return None
        try:
            npz = np.load(str(masks_path))
            masks = {}
            for k in npz.files:
                m = npz[k]
                masks[k] = m if m.shape[:2] == (h, w) else cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
            return masks
        except Exception as e:
            logger.warning(f"Notice loading masks.npz for {photo_id}: {e}")
            return None

    def _render_look(
        self,
        subject_bgr: np.ndarray,
        original_bgr: np.ndarray,
        alpha: np.ndarray,
        face_info: Optional[Dict[str, Any]],
        masks: Optional[Dict[str, np.ndarray]],
        active_settings: Dict[str, Any],
        analysis: Dict[str, Any],
        decontaminate: bool
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Shared render used by both the interactive preview and the full-resolution export.
        Exposure, white balance, retouching, lighting and colour grading run on the subject
        photo first; the backdrop is composited last so the chosen backdrop colour is never
        re-tinted per photo and stays identical across a batch.
        Returns (rendered_bgr, refined_alpha).
        """
        h, w = subject_bgr.shape[:2]
        bg_replacement = active_settings.get("bg_replacement_enabled", True)
        backdrop_mode = active_settings.get("backdrop_mode", "replace" if bg_replacement else "keep")
        backdrop_type = active_settings.get("backdrop_type", "classic_blue")

        base = original_bgr if backdrop_mode == "keep" else subject_bgr
        base = self._apply_auto_corrections(base, analysis)

        # Flyaway hairs against the backdrop are removed by refining the matte around the hair,
        # with the cap and tassel protected.
        hair_mask = masks.get("hair") if masks else None
        if (
            backdrop_mode != "keep"
            and active_settings.get("cleanup_loose_hair", True)
            and hair_mask is not None
            and cv2.countNonZero(hair_mask) > 0
        ):
            alpha = cleanup_flyaway_hair_alpha(
                alpha,
                hair_mask=hair_mask,
                strength=float(active_settings.get("loose_hair_cleanup", 0.40) or 0.0),
                protect_mask=masks.get("hat"),
            )

        preset_id = active_settings.get("preset_id") or active_settings.get("beauty_preset") or "natural"
        preset_id = PRESET_ALIASES.get(preset_id, preset_id)
        enhanced = apply_beauty_preset_to_image(
            base,
            face_info=face_info,
            preset_id=preset_id,
            custom_adjustments=active_settings,
            precomputed_masks=masks,
            subject_mask=alpha,
        )

        if backdrop_mode == "replace":
            backdrop = generate_studio_backdrop(w, h, backdrop_type=backdrop_type, face_info=face_info)
            enhanced = composite_subject_onto_backdrop(enhanced, alpha, backdrop, decontaminate=decontaminate)
        elif backdrop_mode == "clean":
            enhanced = clean_original_backdrop(enhanced, alpha)
        return enhanced, alpha

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

        # Edge-decontaminated copy (precomputed) avoids heavy decontamination per slider move
        clean_preview_p = photo_dir / "preview_clean.jpg"
        clean_subj_bgr = cv2.imread(str(clean_preview_p)) if clean_preview_p.exists() else None
        decontam_needed = clean_subj_bgr is None or clean_subj_bgr.shape[:2] != (ph, pw)
        if decontam_needed:
            clean_subj_bgr = preview_bgr

        preview_masks = self._load_masks(photo_dir / "masks.npz", ph, pw, photo_id)
        enhanced_preview, alpha_preview = self._render_look(
            clean_subj_bgr,
            preview_bgr,
            alpha_preview,
            preview_face_info,
            preview_masks,
            active_settings,
            analysis,
            decontaminate=decontam_needed,
        )

        # 4. Save enhanced preview and crops to disk for immediate serving
        enhanced_path = photo_dir / "preview_enhanced.jpg"
        cv2.imwrite(str(enhanced_path), enhanced_preview, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        try:
            crop_8r = crop_8r_aspect(enhanced_preview)
            cv2.imwrite(str(photo_dir / "preview_8R.jpg"), crop_8r, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            crop_2x2 = crop_2x2_id(enhanced_preview, preview_face_info, mask=alpha_preview)
            cv2.imwrite(str(photo_dir / "preview_2x2.jpg"), crop_2x2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        except Exception as crop_err:
            logger.warning(f"Preview crop precomputation notice for {photo_id}: {crop_err}")

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

        full_masks = self._load_masks(photo_dir / "masks.npz", h, w, photo_id)
        enhanced_bgr, alpha_mask = self._render_look(
            img_bgr,
            img_bgr,
            alpha_mask,
            face_info,
            full_masks,
            active_settings,
            analysis,
            decontaminate=True,
        )

        # 3. Print Crops
        crop_8r = crop_8r_aspect(enhanced_bgr)
        crop_2x2 = crop_2x2_id(enhanced_bgr, face_info, mask=alpha_mask)

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

    def update_photo_settings(
        self,
        project_id: str,
        photo_id: str,
        settings: Dict[str, Any],
        is_user_override: bool = True
    ) -> Dict[str, Any]:
        """Saves custom settings for a specific photo and marks it as user-overridden."""
        from beautification_presets import BEAUTY_PRESETS, PRESET_ALIASES, AFTERSHOOT_COLOR_PROFILES
        from background_engine import STUDIO_BACKDROPS, BACKDROP_ALIASES

        if "preset_id" in settings or "beauty_preset" in settings:
            raw_pid = settings.get("preset_id") or settings.get("beauty_preset")
            pid = PRESET_ALIASES.get(raw_pid, raw_pid)
            if pid not in BEAUTY_PRESETS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown preset: '{raw_pid}'. Valid presets: {list(BEAUTY_PRESETS.keys())}"
                )
            settings["preset_id"] = pid
            settings["beauty_preset"] = pid
        if "backdrop_type" in settings:
            b_id = BACKDROP_ALIASES.get(settings["backdrop_type"], settings["backdrop_type"])
            if b_id not in STUDIO_BACKDROPS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown backdrop_type: '{settings['backdrop_type']}'. Valid backdrops: {list(STUDIO_BACKDROPS.keys())}"
                )
        if "color_profile" in settings and settings["color_profile"] not in AFTERSHOOT_COLOR_PROFILES:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown color_profile: '{settings['color_profile']}'. Valid profiles: {list(AFTERSHOOT_COLOR_PROFILES.keys())}"
            )

        photo_dir = self.get_photo_dir(project_id, photo_id)
        current = self.load_json(photo_dir / "settings.json") or {}
        updated = {**current, **settings, "has_user_override": is_user_override}
        self.save_json(photo_dir / "settings.json", updated)

        meta = self.load_json(photo_dir / "meta.json") or {}
        meta["has_user_override"] = is_user_override
        self.save_json(photo_dir / "meta.json", meta)
        return updated

    def clear_photo_override(self, project_id: str, photo_id: str) -> Dict[str, Any]:
        """Clears user override on a photo so it inherits project-wide looks."""
        return self.update_photo_settings(project_id, photo_id, {}, is_user_override=False)

    def apply_settings_to_project(
        self,
        project_id: str,
        source_photo_id: str,
        exclude_overridden: bool = True
    ) -> Dict[str, Any]:
        """
        Single to Bulk Apply:
        - Copies settings from source photo to every other photo in the project.
        - Preserves per-photo custom overrides if exclude_overridden is True.
        - Triggers fast preview re-renders so per-photo automatic corrections
          (exposure compensation, white balance) harmonize the entire gallery.
        """
        source_dir = self.get_photo_dir(project_id, source_photo_id)
        source_settings = self.load_json(source_dir / "settings.json")
        if not source_settings:
            raise FileNotFoundError(f"Source settings not found for photo {source_photo_id}")

        # Remove local override flag from look template
        template = dict(source_settings)
        template["has_user_override"] = False

        project_dir = self.get_project_dir(project_id)
        updated_photos: List[str] = []
        skipped_photos: List[str] = []

        for p_dir in project_dir.iterdir():
            if not p_dir.is_dir() or not (p_dir / "original.jpg").exists():
                continue
            pid = p_dir.name
            if pid == source_photo_id:
                continue

            target_settings = self.load_json(p_dir / "settings.json") or {}
            target_meta = self.load_json(p_dir / "meta.json") or {}

            is_overridden = bool(
                target_settings.get("has_user_override", False) or
                target_meta.get("has_user_override", False)
            )

            if exclude_overridden and is_overridden:
                skipped_photos.append(pid)
                continue

            # Apply shared look settings to target photo
            merged = {**target_settings, **template, "has_user_override": False}
            self.save_json(p_dir / "settings.json", merged)

            # Re-render preview with per-photo auto-harmonization
            try:
                self.render_preview_fast(project_id, pid, custom_settings=merged)
            except Exception as e:
                logger.warning(f"Preview re-render notice for {pid}: {e}")

            updated_photos.append(pid)

        return {
            "project_id": project_id,
            "source_photo_id": source_photo_id,
            "updated_count": len(updated_photos),
            "skipped_count": len(skipped_photos),
            "updated_photo_ids": updated_photos,
            "skipped_photo_ids": skipped_photos
        }

    def list_projects(self, studio_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all existing projects in store belonging to studio_id (or all if None)."""
        if not self.base_dir.exists():
            return []
        projects = []
        for p_dir in self.base_dir.iterdir():
            if p_dir.is_dir() and not p_dir.name.startswith("."):
                project_meta = self.load_json(p_dir / "project.json") or {}
                owner_studio = project_meta.get("owner_studio_id", "default_studio")
                if studio_id is not None and owner_studio != studio_id:
                    continue
                photos = self.list_photos(p_dir.name)
                projects.append({
                    "id": p_dir.name,
                    "title": project_meta.get("title", p_dir.name.replace("_", " ").title()),
                    "owner_studio_id": owner_studio,
                    "photo_count": len(photos),
                    "created_at": project_meta.get("created_at", time.time())
                })
        return projects

    def get_or_create_project(
        self,
        project_id: str,
        title: Optional[str] = None,
        studio_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Gets or creates project directory with metadata and owner studio_id."""
        validate_id(project_id, "project_id")
        p_dir = self.get_project_dir(project_id)
        meta_file = p_dir / "project.json"
        meta = self.load_json(meta_file)
        if not meta:
            meta = {
                "id": project_id,
                "title": title or project_id.replace("_", " ").title(),
                "owner_studio_id": studio_id or "default_studio",
                "created_at": time.time()
            }
            self.save_json(meta_file, meta)
        elif studio_id and not meta.get("owner_studio_id"):
            meta["owner_studio_id"] = studio_id
            self.save_json(meta_file, meta)
        return meta

    def get_project(self, project_id: str, studio_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieves project metadata. If studio_id provided, asserts ownership."""
        validate_id(project_id, "project_id")
        p_dir = (self.base_dir / project_id).resolve()
        if not p_dir.is_relative_to(self.base_dir):
            raise HTTPException(status_code=400, detail="Security violation: Path traversal detected")
        meta_file = p_dir / "project.json"
        if not meta_file.exists():
            if p_dir.exists() and any(p_dir.iterdir()):
                return self.get_or_create_project(project_id, studio_id=studio_id)
            return None
        meta = self.load_json(meta_file) or {}
        if studio_id and meta.get("owner_studio_id") and meta.get("owner_studio_id") != studio_id:
            return None
        return meta

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
                    "has_user_override": bool(settings.get("has_user_override", False) or meta.get("has_user_override", False)),
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
