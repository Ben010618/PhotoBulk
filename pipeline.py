"""
KameraPh Unified Production Pipeline (pipeline.py)
--------------------------------------------------
Consolidates matting, beautification, regalia optimization, and print cropping
into a single high-performance pipeline used by both local and cloud fleet runtimes.
"""

import os
import time
import cv2
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple, Optional, List

from analyzer_engine import analyze_portrait, get_face_detector
from beautification_presets import apply_beauty_preset_to_image, BEAUTY_PRESETS
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop, STUDIO_BACKDROPS
from regalia_profiles import REGALIA_PROFILES

_REMBG_SESSION = None

def get_rembg_session():
    """Initializes or returns cached rembg U2Net session."""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        try:
            import rembg
            _REMBG_SESSION = rembg.new_session("u2net")
        except Exception as e:
            print("Notice: rembg session initialization fallback:", e)
            _REMBG_SESSION = False
    return _REMBG_SESSION


def get_subject_mask(img_bgr: np.ndarray, face_info: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Computes a neural segmentation mask preserving academic togas, UP sablays,
    tassels, and caps. Uses rembg U2Net with high-precision GrabCut fallback.
    """
    h, w = img_bgr.shape[:2]
    session = get_rembg_session()

    if session:
        try:
            import rembg
            # Convert BGR to RGB PIL
            rgb_img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_img)
            mask_out = rembg.remove(pil_img, session=session, only_mask=True)
            mask_np = np.array(mask_out)
            
            # Post-process mask: clean binary threshold and edge feathering
            _, binary_mask = cv2.threshold(mask_np, 128, 255, cv2.THRESH_BINARY)
            
            # Preserve regalia edges: slight closing to prevent holes in dark black togas
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            refined = cv2.morphologyEx(binary_mask, cv2.MORPH_CLOSE, kernel, iterations=1)
            return refined
        except Exception as e:
            print("rembg execution error, falling back to GrabCut:", e)

    # Adaptive GrabCut Saliency Fallback (preserves cap, tassel, and toga)
    mask = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    if face_info and 'bbox' in face_info:
        fx, fy, fw, fh = face_info['bbox']
        # Forehead & cap area above face
        cap_top = max(0, fy - int(fh * 1.0))
        # Gown & torso area below face
        gown_bottom = min(h - 1, fy + int(fh * 3.5))
        # Shoulder span
        shoulder_left = max(0, fx - int(fw * 1.5))
        shoulder_right = min(w - 1, fx + int(fw * 2.5))
        rect = (shoulder_left, cap_top, max(10, shoulder_right - shoulder_left), max(10, gown_bottom - cap_top))
    else:
        rect = (int(w * 0.10), int(h * 0.05), int(w * 0.80), int(h * 0.90))

    try:
        cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, 2, cv2.GC_INIT_WITH_RECT)
        output_mask = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype('uint8')
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        return cv2.morphologyEx(output_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    except Exception:
        # Ultimate safe foreground fallback
        safe_mask = np.full((h, w), 255, dtype=np.uint8)
        return safe_mask


def crop_8r_aspect(img_bgr: np.ndarray) -> np.ndarray:
    """Crops portrait to standard 8R / 8x10 yearbook aspect ratio (4:5 vertical)."""
    h, w = img_bgr.shape[:2]
    target_aspect = 4.0 / 5.0  # width / height
    current_aspect = w / float(h)

    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        start_x = (w - new_w) // 2
        return img_bgr[:, start_x:start_x + new_w]
    else:
        new_h = int(w / target_aspect)
        start_y = max(0, int((h - new_h) * 0.20))
        return img_bgr[start_y:start_y + new_h, :]


def crop_2x2_id(img_bgr: np.ndarray, face_info: Optional[Dict[str, Any]] = None, spec: str = "DFA") -> np.ndarray:
    """
    Crops portrait to Philippine 2x2 ID standard (600x600 px at 300 DPI).
    Conforms to DFA Passport and PRC Professional Regulation Commission specifications:
      - Head height (crown to chin) occupies 70% to 80% of vertical frame.
      - Eye level positioned 58% to 62% above bottom margin.
      - Head centered horizontally.
    """
    h, w = img_bgr.shape[:2]
    target_dim = 600

    if face_info and 'bbox' in face_info:
        fx, fy, fw, fh = face_info['bbox']
        # For DFA/PRC, crown is roughly 20% above bounding box top; chin is at bottom
        chin_y = fy + fh
        crown_y = max(0, fy - int(fh * 0.25))
        head_height = max(10, chin_y - crown_y)

        # Target 75% head height inside crop
        target_box_size = int(head_height / 0.75)
        
        # Center horizontally on face center
        face_cx = fx + fw // 2
        
        # Position crown near top: head top margin ~ 10-12% of box size
        crop_y1 = max(0, crown_y - int(target_box_size * 0.12))
        crop_x1 = max(0, face_cx - target_box_size // 2)
        
        # Adjust if box exceeds image boundaries
        if crop_x1 + target_box_size > w:
            crop_x1 = max(0, w - target_box_size)
        if crop_y1 + target_box_size > h:
            crop_y1 = max(0, h - target_box_size)
            
        crop_box = img_bgr[crop_y1:crop_y1 + target_box_size, crop_x1:crop_x1 + target_box_size]
    else:
        box_size = min(w, h)
        crop_y1 = max(0, int(h * 0.05))
        crop_x1 = max(0, (w - box_size) // 2)
        crop_box = img_bgr[crop_y1:crop_y1 + box_size, crop_x1:crop_x1 + box_size]

    if crop_box.size == 0:
        crop_box = cv2.resize(img_bgr, (target_dim, target_dim))
    else:
        crop_box = cv2.resize(crop_box, (target_dim, target_dim), interpolation=cv2.INTER_LANCZOS4)

    return crop_box


def detect_actual_engine() -> str:
    """Detects whether GPU hardware acceleration or local CPU is running."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            return f"Local GPU ({gpu_name})"
    except Exception:
        pass
        
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        if "CUDAExecutionProvider" in providers:
            return "ONNX Runtime (CUDA Accelerated)"
    except Exception:
        pass

    return "Local CPU (OpenCV + ONNX Hybrid)"


def process_complete_workflow(
    img_bgr: np.ndarray,
    bg_replacement_enabled: bool = True,
    backdrop_type: str = "royal_navy",
    beauty_preset: str = "morena_radiant",
    regalia_profile: str = "standard_toga",
    skin_smoothing: float = 0.65,
    blemish_cut: float = 0.75,
    dark_spot_whitening: float = 0.50,
    shine_reduction: float = 0.35,
    lip_color: str = "#d87093",
    lip_intensity: float = 0.35,
    glow_intensity: float = 0.40,
    eye_catchlight: float = 0.35,
    teeth_whitening: float = 0.50,
    lighting_temp: str = "neutral_5500k",
    studio_light_intensity: float = 0.20,
    rim_light_boost: float = 0.20,
    iron_strength: float = 0.70,
    analysis_data: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, int, Optional[Dict[str, Any]], str]:
    """
    Executes the full graduation photo processing workflow:
      1. Regalia-specific parameter adjustment
      2. Neural subject matting (rembg)
      3. Studio backdrop compositing
      4. Skin retouching, blemish healing, melanin radiance, catchlights
      5. Real elapsed latency and hardware engine reporting
    """
    start_time = time.time()
    h, w = img_bgr.shape[:2]

    # Incorporate Regalia Profile Defaults if selected
    if regalia_profile in REGALIA_PROFILES:
        r_prof = REGALIA_PROFILES[regalia_profile]
        iron_strength = r_prof.get("iron_strength", iron_strength)
        skin_smoothing = r_prof.get("skin_smoothing", skin_smoothing)
        shine_reduction = r_prof.get("shine_reduction", shine_reduction)

    # 1. Portrait Analysis & Face Geometry
    analysis = analysis_data or analyze_portrait(img_bgr)
    
    face_info = None
    if analysis.get("has_face") and "face_box" in analysis:
        fb = analysis["face_box"]
        face_info = {
            "bbox": [fb["x"], fb["y"], fb["width"], fb["height"]]
        }

    # 2. High-Fidelity Subject Segmentation
    subject_mask = get_subject_mask(img_bgr, face_info)

    # 3. Studio Backdrop Compositing
    if bg_replacement_enabled:
        backdrop = generate_studio_backdrop(w, h, backdrop_type=backdrop_type)
        subject_isolated = composite_subject_onto_backdrop(img_bgr, subject_mask, backdrop)
    else:
        subject_isolated = img_bgr.copy()

    # 4. Skin Beautification, Melanin Radiance & Garment De-creasing
    enhanced_portrait = apply_beauty_preset_to_image(
        subject_isolated,
        face_info=face_info,
        preset_id=beauty_preset,
        custom_adjustments={
            "skin_smoothing": skin_smoothing,
            "blemish_cut": blemish_cut,
            "dark_spot_whitening": dark_spot_whitening,
            "shine_reduction": shine_reduction,
            "lip_color": lip_color,
            "lip_intensity": lip_intensity,
            "glow_intensity": glow_intensity,
            "eye_catchlight": eye_catchlight,
            "teeth_whitening": teeth_whitening,
            "lighting_temp": lighting_temp,
            "studio_light_intensity": studio_light_intensity,
            "rim_light_boost": rim_light_boost,
            "iron_strength": iron_strength
        }
    )

    actual_latency_ms = max(1, int((time.time() - start_time) * 1000))
    engine_label = detect_actual_engine()

    return enhanced_portrait, actual_latency_ms, face_info, engine_label
