"""
KameraPh Unified Production Pipeline (pipeline.py)
--------------------------------------------------
Consolidates matting, beautification, regalia optimization, and print cropping
into a single high-performance pipeline used by both local and cloud fleet runtimes.
"""

import os
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Union
import cv2
import numpy as np
import qrcode
from PIL import Image
from pydantic import BaseModel, Field

from analyzer_engine import analyze_portrait, get_face_detector, load_portrait_image_safely
from beautification_presets import apply_beauty_preset_to_image, BEAUTY_PRESETS
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop, STUDIO_BACKDROPS, clean_original_backdrop
from regalia_profiles import REGALIA_PROFILES
import config

PROOF_BASE_URL = os.environ.get("PROOF_BASE_URL", "http://127.0.0.1:8000/proof")


def generate_watermarked_proof(
    img_bgr: np.ndarray, 
    student_name: str = "Juan Dela Cruz", 
    section: str = "STEM-12A", 
    student_id: str = "LRN-10928374",
    school_name: str = "Manila Science High School",
    watermark_label: str = "KAMERAPH STUDIO PROOF"
) -> np.ndarray:
    """
    Generates a secure, branded studio proof with:
      1. Semi-transparent diagonal watermark across the portrait.
      2. Bottom metadata footer with student credentials and school name.
      3. Embedded high-contrast QR code pointing to active proof verification portal.
    """
    h, w = img_bgr.shape[:2]
    proof = img_bgr.copy()
    
    # 1. Semi-transparent diagonal watermark overlay
    overlay = proof.copy()
    font = cv2.FONT_HERSHEY_DUPLEX
    
    # Draw repeating diagonal text
    for y_pos in range(int(h * 0.22), int(h * 0.88), 170):
        cv2.putText(overlay, watermark_label, (int(w * 0.06), y_pos), font, 0.95, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(overlay, "DO NOT PRINT OR SCREENSHOT", (int(w * 0.10), y_pos + 42), font, 0.60, (220, 220, 220), 1, cv2.LINE_AA)
        
    # Alpha blend overlay onto proof at 30% opacity
    cv2.addWeighted(overlay, 0.30, proof, 0.70, 0, proof)
    
    # 2. Branded Bottom Studio Card (110px height)
    card_h = 110
    card = np.zeros((card_h, w, 3), dtype=np.uint8)
    card[:] = (18, 22, 30) # Dark surface #161b22
    
    # Generate high-contrast student QR code pointing to real verification route
    clean_id = student_id.replace(" ", "_")
    qr_payload = f"{PROOF_BASE_URL}/{clean_id}"
    qr = qrcode.QRCode(box_size=3, border=2)
    qr.add_data(qr_payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_np = cv2.cvtColor(np.array(qr_img), cv2.COLOR_RGB2BGR)
    qr_h, qr_w = qr_np.shape[:2]
    
    # Place QR code badge on the right side of the footer card
    qr_x = w - qr_w - 18
    qr_y = (card_h - qr_h) // 2
    if qr_h <= card_h and qr_x > 0:
        card[qr_y:qr_y+qr_h, qr_x:qr_x+qr_w] = qr_np
    
    # Draw Student Credentials & Studio Info
    cv2.putText(card, student_name.upper(), (22, 36), font, 0.72, (240, 246, 252), 2, cv2.LINE_AA)
    cv2.putText(card, f"{school_name}  *  {section}", (22, 63), font, 0.48, (139, 148, 158), 1, cv2.LINE_AA)
    cv2.putText(card, f"LRN / ID: {student_id}  |  Scan QR for Verification", (22, 88), font, 0.40, (110, 118, 129), 1, cv2.LINE_AA)
    
    # Subtle top divider line #30363d
    cv2.line(card, (0, 0), (w, 0), (48, 54, 61), 1)
    
    # Combine Portrait + Bottom Proofing Card
    final_proof = np.vstack([proof, card])
    return final_proof

logger = logging.getLogger("kameraph.pipeline")


class ProcessingParams(BaseModel):
    bg_replacement_enabled: bool = True
    backdrop_type: str = "royal_navy"
    beauty_preset: str = "morena_radiant"
    regalia_profile: str = "standard_toga"
    skin_smoothing: float = Field(default=0.50, ge=0.0, le=1.0)
    blemish_cut: float = Field(default=0.60, ge=0.0, le=1.0)
    spot_correction: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    dark_spot_whitening: float = Field(default=0.40, ge=0.0, le=1.0)
    keep_moles: bool = True
    loose_hair_cleanup: float = Field(default=0.40, ge=0.0, le=1.0)
    cleanup_loose_hair: bool = True
    shine_reduction: float = Field(default=0.30, ge=0.0, le=1.0)
    lip_color: str = "#d87093"
    lip_intensity: float = Field(default=0.0, ge=0.0, le=1.0)
    glow_intensity: float = Field(default=0.20, ge=0.0, le=1.0)
    eye_catchlight: float = Field(default=0.20, ge=0.0, le=1.0)
    teeth_whitening: float = Field(default=0.40, ge=0.0, le=1.0)
    lighting_temp: str = "neutral_5500k"
    studio_light_intensity: float = Field(default=0.20, ge=0.0, le=1.0)
    rim_light_boost: float = Field(default=0.18, ge=0.0, le=1.0)
    iron_strength: float = Field(default=0.70, ge=0.0, le=1.0)
    output_directory: Optional[str] = None
    save_crops: bool = True
    save_proof: bool = False
    student_name: str = "Juan Dela Cruz"
    student_id: Optional[str] = None


class ProcessedImageResult(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    success: bool
    latency_ms: int = 0
    engine_used: str = "Local CPU (OpenCV + ONNX Hybrid)"
    enhanced_image_path: Optional[str] = None
    crop_8r_path: Optional[str] = None
    crop_2x2_path: Optional[str] = None
    proof_path: Optional[str] = None
    analysis: Dict[str, Any] = Field(default_factory=dict)
    face_info: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    enhanced_bgr: Optional[np.ndarray] = Field(default=None, exclude=True)
    crop_8r_bgr: Optional[np.ndarray] = Field(default=None, exclude=True)
    crop_2x2_bgr: Optional[np.ndarray] = Field(default=None, exclude=True)
    proof_bgr: Optional[np.ndarray] = Field(default=None, exclude=True)


_REMBG_SESSION = None
_REMBG_SESSION_NAME = None

def get_rembg_session(model_name: Optional[str] = None):
    """Initializes or returns cached rembg session, trying specified model or config.REMBG_MODEL, with fallback to u2net."""
    global _REMBG_SESSION, _REMBG_SESSION_NAME
    target_model = model_name or getattr(config, "REMBG_MODEL", "u2net")
    if _REMBG_SESSION is not None and _REMBG_SESSION_NAME == target_model and _REMBG_SESSION is not False:
        return _REMBG_SESSION

    try:
        import rembg
        try:
            _REMBG_SESSION = rembg.new_session(target_model)
            _REMBG_SESSION_NAME = target_model
            return _REMBG_SESSION
        except Exception as e:
            print(f"Notice: Failed to load rembg session '{target_model}': {e}. Falling back to 'u2net'...")
            _REMBG_SESSION = rembg.new_session("u2net")
            _REMBG_SESSION_NAME = "u2net"
            return _REMBG_SESSION
    except Exception as e:
        print("Notice: rembg session initialization fallback:", e)
        _REMBG_SESSION = False
        _REMBG_SESSION_NAME = None
    return _REMBG_SESSION


def get_subject_mask(img_bgr: np.ndarray, face_info: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """
    Computes a neural segmentation mask preserving academic togas, UP sablays,
    tassels, and caps with a fractional soft alpha matte.
    Uses rembg (u2net / birefnet-portrait) with adaptive feathered GrabCut fallback.
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
            
            # Preserve soft alpha transitions: do NOT threshold to pure binary 0/255.
            # Clean up residual background noise (< 4) while preserving hair/tassel gradients:
            cleaned_mask = np.where(mask_np < 4, 0, mask_np)
            return cleaned_mask.astype(np.uint8)
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
        closed = cv2.morphologyEx(output_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        # Soften edges slightly so fallback also provides fractional transitions
        feathered = cv2.GaussianBlur(closed, (7, 7), 1.5)
        edge_zone = cv2.Canny(closed, 100, 200)
        edge_dilated = cv2.dilate(edge_zone, np.ones((5, 5), np.uint8), iterations=1)
        soft_fallback = np.where(edge_dilated > 0, feathered, closed)
        return soft_fallback.astype(np.uint8)
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
    backdrop_type: str = "classic_blue",
    beauty_preset: str = "natural",
    regalia_profile: Optional[str] = "standard_toga",
    skin_smoothing: Optional[float] = None,
    blemish_cut: Optional[float] = None,
    spot_correction: Optional[float] = None,
    dark_spot_whitening: Optional[float] = None,
    shine_reduction: Optional[float] = None,
    lip_color: Optional[str] = None,
    lip_intensity: Optional[float] = None,
    glow_intensity: Optional[float] = None,
    eye_catchlight: Optional[float] = None,
    teeth_whitening: Optional[float] = None,
    lighting_temp: str = "neutral_5500k",
    studio_light_intensity: Optional[float] = None,
    rim_light_boost: Optional[float] = None,
    iron_strength: Optional[float] = None,
    analysis_data: Optional[Dict[str, Any]] = None,
    backdrop_mode: Optional[str] = None,
    loose_hair_cleanup: Optional[float] = None,
    keep_moles: bool = True
) -> Tuple[np.ndarray, int, Optional[Dict[str, Any]], str]:
    """
    Executes the full graduation photo processing workflow:
      1. Regalia-specific default parameters (defaults only, never overwriting user sliders)
      2. Neural subject matting (rembg soft alpha + optional flyaway hair smoothing)
      3. Studio backdrop compositing (replace, clean original, or keep)
      4. Smart auto-corrections from portrait analysis
      5. Semantic face-parsing retouching, blemish healing (preserving moles), even skin tone
      6. Real elapsed latency and hardware engine reporting
    """
    start_time = time.time()
    h, w = img_bgr.shape[:2]

    # Regalia Profile: use profile values ONLY as defaults if user has not set custom values
    r_prof = REGALIA_PROFILES.get(regalia_profile, {}) if regalia_profile else {}
    if iron_strength is None:
        iron_strength = r_prof.get("iron_strength", 0.70)
    if skin_smoothing is None:
        skin_smoothing = r_prof.get("skin_smoothing", 0.50)
    if blemish_cut is None:
        blemish_cut = r_prof.get("blemish_cut", 0.60)
    if spot_correction is None:
        spot_correction = dark_spot_whitening if dark_spot_whitening is not None else r_prof.get("dark_spot_whitening", 0.40)
    if shine_reduction is None:
        shine_reduction = r_prof.get("shine_reduction", 0.30)
    if studio_light_intensity is None:
        studio_light_intensity = 0.20
    if rim_light_boost is None:
        rim_light_boost = 0.18
    if glow_intensity is None:
        glow_intensity = 0.20
    if eye_catchlight is None:
        eye_catchlight = 0.20
    if teeth_whitening is None:
        teeth_whitening = 0.40
    if lip_intensity is None:
        lip_intensity = 0.0

    # 1. Portrait Analysis & Face Geometry
    analysis = analysis_data or analyze_portrait(img_bgr)
    
    face_info = None
    if analysis.get("has_face") and "face_box" in analysis:
        fb = analysis["face_box"]
        face_info = {
            "bbox": [fb["x"], fb["y"], fb["width"], fb["height"]]
        }
        if analysis.get("landmarks"):
            face_info.update(analysis["landmarks"])
    else:
        # Mark photo "needs review" when no face is found
        analysis["review_needed"] = True
        if not analysis.get("review_reason"):
            analysis["review_reason"] = "No clear face detected in portrait. Requires manual review."

    # 2. High-Fidelity Subject Segmentation (fractional soft alpha)
    subject_mask = get_subject_mask(img_bgr, face_info)

    # Loose flyaway hair smoothing on outer silhouette
    if loose_hair_cleanup and loose_hair_cleanup > 0.05:
        from beautification_presets import cleanup_flyaway_hair_alpha
        subject_mask = cleanup_flyaway_hair_alpha(subject_mask, strength=loose_hair_cleanup)

    # 3. Studio Backdrop Handling ('replace', 'clean', or 'keep')
    mode = backdrop_mode or ("replace" if bg_replacement_enabled else "keep")
    if mode == "clean":
        subject_isolated = clean_original_backdrop(img_bgr, subject_mask)
    elif mode == "replace":
        backdrop = generate_studio_backdrop(w, h, backdrop_type=backdrop_type, face_info=face_info)
        subject_isolated = composite_subject_onto_backdrop(img_bgr, subject_mask, backdrop)
    else:
        subject_isolated = img_bgr.copy()

    # 4. Smart Auto-Corrections (Exposure & Tone)
    if analysis and "auto_corrections" in analysis:
        auto_c = analysis["auto_corrections"]
        ev = float(auto_c.get("exposure_compensation_ev", 0.0))
        if abs(ev) >= 0.10:
            factor = float(np.clip(2.0 ** (ev * 0.75), 0.70, 1.45))
            subject_isolated = np.clip(subject_isolated.astype(np.float32) * factor, 0.0, 255.0).astype(np.uint8)

    # 5. Skin Beautification, Melanin Radiance & Garment De-creasing
    if face_info is None:
        # When no face is found, skip facial steps but run studio lighting and grading
        from beautification_presets import apply_studio_environment_lighting
        subject_isolated_f = subject_isolated.astype(np.float32)
        lit_bgr = apply_studio_environment_lighting(
            subject_isolated_f,
            subject_mask,
            lighting_temp=lighting_temp,
            studio_light_intensity=studio_light_intensity,
            rim_light_boost=rim_light_boost
        )
        enhanced_portrait = np.clip(lit_bgr, 0, 255).astype(np.uint8)
    else:
        enhanced_portrait = apply_beauty_preset_to_image(
            subject_isolated,
            face_info=face_info,
            preset_id=beauty_preset,
            custom_adjustments={
                "skin_smoothing": skin_smoothing,
                "blemish_cut": blemish_cut,
                "spot_correction": spot_correction,
                "dark_spot_whitening": spot_correction,
                "shine_reduction": shine_reduction,
                "lip_color": lip_color,
                "lip_intensity": lip_intensity,
                "glow_intensity": glow_intensity,
                "eye_catchlight": eye_catchlight,
                "teeth_whitening": teeth_whitening,
                "lighting_temp": lighting_temp,
                "studio_light_intensity": studio_light_intensity,
                "rim_light_boost": rim_light_boost,
                "iron_strength": iron_strength,
                "loose_hair_cleanup": loose_hair_cleanup or 0.40,
                "keep_moles": keep_moles
            }
        )

    actual_latency_ms = max(1, int((time.time() - start_time) * 1000))
    engine_label = detect_actual_engine()

    return enhanced_portrait, actual_latency_ms, face_info, engine_label


def process_image(
    image_input: Union[str, Path, np.ndarray],
    parameters: Optional[ProcessingParams] = None
) -> ProcessedImageResult:
    """
    Standardized, type-hinted entry point for the KameraPh ML Vision Pipeline.
    Supports file paths (str/Path) and in-memory arrays (np.ndarray).
    Returns structured ProcessedImageResult with metadata, crops, and optional disk artifacts.
    """
    start_time = time.time()
    params = parameters or ProcessingParams()
    engine_label = detect_actual_engine()

    try:
        # 1. Safe Image Resolution
        img_bgr = load_portrait_image_safely(image_input)
    except FileNotFoundError as e:
        logger.error(f"[pipeline] Input image file not found: {image_input}")
        return ProcessedImageResult(
            success=False,
            latency_ms=0,
            engine_used=engine_label,
            error=f"Image file not found: {image_input}"
        )
    except Exception as e:
        logger.error(f"[pipeline] Failed to load image {image_input}: {e}\n{traceback.format_exc()}")
        return ProcessedImageResult(
            success=False,
            latency_ms=0,
            engine_used=engine_label,
            error=f"Image decode failure: {str(e)}"
        )

    try:
        # 1.5 Portrait Quality Analysis (Run once on input portrait)
        analysis = analyze_portrait(img_bgr)

        # 2. Run Complete Workflow
        enhanced_bgr, workflow_latency_ms, face_info, engine_label = process_complete_workflow(
            img_bgr,
            analysis_data=analysis,
            bg_replacement_enabled=params.bg_replacement_enabled,
            backdrop_type=params.backdrop_type,
            beauty_preset=params.beauty_preset,
            regalia_profile=params.regalia_profile,
            skin_smoothing=params.skin_smoothing,
            blemish_cut=params.blemish_cut,
            spot_correction=params.spot_correction,
            dark_spot_whitening=params.dark_spot_whitening,
            shine_reduction=params.shine_reduction,
            lip_color=params.lip_color,
            lip_intensity=params.lip_intensity,
            glow_intensity=params.glow_intensity,
            eye_catchlight=params.eye_catchlight,
            teeth_whitening=params.teeth_whitening,
            lighting_temp=params.lighting_temp,
            studio_light_intensity=params.studio_light_intensity,
            rim_light_boost=params.rim_light_boost,
            iron_strength=params.iron_strength,
            loose_hair_cleanup=params.loose_hair_cleanup,
            keep_moles=params.keep_moles
        )

        # 3. Compute High-Precision Standard Prints
        crop_8r = crop_8r_aspect(enhanced_bgr)
        crop_2x2 = crop_2x2_id(enhanced_bgr, face_info)
        proof_bgr = None

        if params.save_proof:
            proof_bgr = generate_watermarked_proof(
                enhanced_bgr,
                student_name=params.student_name,
                student_id=params.student_id or "STUDIO_PROOF"
            )

        # 4. Optional Safe Disk Export
        enhanced_path = None
        crop_8r_path = None
        crop_2x2_path = None
        proof_path = None

        if params.output_directory:
            out_dir = Path(params.output_directory)
            out_dir.mkdir(parents=True, exist_ok=True)

            base_name = Path(image_input).stem if isinstance(image_input, (str, Path)) else "processed_portrait"

            p_enhanced = out_dir / f"{base_name}_enhanced.jpg"
            cv2.imwrite(str(p_enhanced), enhanced_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            enhanced_path = str(p_enhanced)

            if params.save_crops:
                p_8r = out_dir / f"{base_name}_8R.jpg"
                cv2.imwrite(str(p_8r), crop_8r, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                crop_8r_path = str(p_8r)

                p_2x2 = out_dir / f"{base_name}_2x2.jpg"
                cv2.imwrite(str(p_2x2), crop_2x2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                crop_2x2_path = str(p_2x2)

            if params.save_proof and proof_bgr is not None:
                p_proof = out_dir / f"{base_name}_proof.jpg"
                cv2.imwrite(str(p_proof), proof_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                proof_path = str(p_proof)

        total_latency_ms = max(1, int((time.time() - start_time) * 1000))

        return ProcessedImageResult(
            success=True,
            latency_ms=total_latency_ms,
            engine_used=engine_label,
            enhanced_image_path=enhanced_path,
            crop_8r_path=crop_8r_path,
            crop_2x2_path=crop_2x2_path,
            proof_path=proof_path,
            analysis=analysis,
            face_info=face_info,
            enhanced_bgr=enhanced_bgr,
            crop_8r_bgr=crop_8r,
            crop_2x2_bgr=crop_2x2,
            proof_bgr=proof_bgr
        )
    except Exception as e:
        logger.error(f"[pipeline] Execution error during processing: {e}\n{traceback.format_exc()}")
        return ProcessedImageResult(
            success=False,
            latency_ms=int((time.time() - start_time) * 1000),
            engine_used=engine_label,
            error=f"Processing failure: {str(e)}"
        )
