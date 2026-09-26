"""
KameraPh Studio Backdrop & Neural Compositing Engine
---------------------------------------------------
Generates authentic Philippine graduation studio backdrops with smooth radial gradients,
strobe spotlights positioned from detected face coordinates, fine dither grain,
contact shadows, edge color decontamination, and 'clean original' backdrop smoothing.
"""

import os
from typing import Optional, Dict, Any
import cv2
import numpy as np

# Clean studio backdrops tailored for formal Philippine graduation and board exam portraits
STUDIO_BACKDROPS = {
    "classic_blue": {
        "id": "classic_blue",
        "name": "Classic Graduation Blue Gradient",
        "description": "Rich studio cobalt and royal blue radial gradient with soft strobe key-light falloff. Standard for UP, UST, Ateneo, and DLSU portraits.",
        "hex": "#1d457a",
        "file": "studio_backdrop_royal_navy.jpg",
        "spot_bgr": (144, 84, 43),   # Center light BGR
        "outer_bgr": (48, 28, 15)     # Deep edge vignette BGR
    },
    "deep_navy": {
        "id": "deep_navy",
        "name": "Deep Academic Navy",
        "description": "Formal deep navy muslin with subtle strobe vignette behind the head.",
        "hex": "#101e33",
        "file": None,
        "spot_bgr": (95, 52, 28),
        "outer_bgr": (32, 17, 10)
    },
    "neutral_grey": {
        "id": "neutral_grey",
        "name": "Neutral Studio Grey",
        "description": "Clean contemporary editorial studio grey with smooth light center.",
        "hex": "#5e656d",
        "file": None,
        "spot_bgr": (155, 148, 142),
        "outer_bgr": (68, 62, 58)
    },
    "studio_white": {
        "id": "studio_white",
        "name": "Studio Pure White (Formal / Passport)",
        "description": "High-key clean seamless white studio background with gentle corner falloff for DFA/PRC passport and formal archives.",
        "hex": "#f5f6f8",
        "file": None,
        "spot_bgr": (252, 252, 252),
        "outer_bgr": (230, 230, 232)
    },
    "warm_brown": {
        "id": "warm_brown",
        "name": "Warm Studio Brown Canvas",
        "description": "Traditional warm mocha/chestnut painted portrait canvas with soft strobe backlight.",
        "hex": "#3d2a1d",
        "file": None,
        "spot_bgr": (55, 75, 105),
        "outer_bgr": (20, 28, 42)
    },
    "prc_red": {
        "id": "prc_red",
        "name": "PRC Crimson",
        "description": "Official Philippine Professional Regulation Commission (PRC) Board Exam crimson red background.",
        "hex": "#8a141b",
        "file": None,
        "spot_bgr": (36, 26, 160),
        "outer_bgr": (14, 9, 72)
    }
}

# Aliases for backward compatibility
BACKDROP_ALIASES = {
    "royal_navy": "classic_blue",
    "mottled_navy": "classic_blue",
    "slate_gray": "neutral_grey",
    "warm_amber": "warm_brown",
    "organic_texture": "neutral_grey"
}


def decontaminate_edges(subject_bgr: np.ndarray, alpha_mask: np.ndarray, radius_px: int = 7) -> np.ndarray:
    """
    Decontaminates color fringe around subject boundaries (hair strands, ears, shoulders, tassels).
    Removes background color bleed from the original studio wall by unmixing and extending
    the true foreground chrominance and luminance across the transition zone.
    """
    if len(alpha_mask.shape) == 3:
        alpha_mask = cv2.cvtColor(alpha_mask, cv2.COLOR_BGR2GRAY)

    # Identify transition band (fractional alpha where bleed occurs)
    transition = ((alpha_mask > 8) & (alpha_mask < 240)).astype(np.uint8)
    if not np.any(transition):
        return subject_bgr.copy()

    alpha = (alpha_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
    bg_mask = (alpha_mask <= 8).astype(np.float32)
    solid_fg = (alpha_mask >= 200).astype(np.float32)

    subj_f = subject_bgr.astype(np.float32)
    ksize = radius_px * 2 + 1

    # 1. Estimate local old background color
    bg_weighted = cv2.boxFilter(subj_f * bg_mask[:, :, np.newaxis], -1, (ksize, ksize))
    bg_norm = cv2.boxFilter(bg_mask, -1, (ksize, ksize))[:, :, np.newaxis]
    bg_norm = np.maximum(bg_norm, 1e-4)
    estimated_old_bg = bg_weighted / bg_norm

    # 2. Unmix foreground color: F = (C - (1 - alpha) * B_old) / alpha
    alpha_clamped = np.maximum(alpha, 0.25)
    unmixed_fg = np.clip((subj_f - (1.0 - alpha) * estimated_old_bg) / alpha_clamped, 0.0, 255.0)

    # 3. Color extension from solid foreground to protect fine hair strands
    fg_weighted = cv2.boxFilter(subj_f * solid_fg[:, :, np.newaxis], -1, (ksize, ksize))
    fg_norm = cv2.boxFilter(solid_fg, -1, (ksize, ksize))[:, :, np.newaxis]
    fg_norm = np.maximum(fg_norm, 1e-4)
    extended_fg = fg_weighted / fg_norm

    # 4. Smooth blend in transition zone
    blend_factor = np.clip((alpha - 0.1) / 0.5, 0.0, 1.0)
    cleaned_transition = blend_factor * unmixed_fg + (1.0 - blend_factor) * extended_fg

    trans_weight = (transition[:, :, np.newaxis] > 0).astype(np.float32)
    decontaminated = subj_f * (1.0 - trans_weight) + cleaned_transition * trans_weight
    return np.clip(decontaminated, 0.0, 255.0).astype(np.uint8)


def clean_original_backdrop(img_bgr: np.ndarray, alpha_mask: np.ndarray) -> np.ndarray:
    """
    Cleans up the original studio backdrop by evening out blotches, wrinkles,
    and harsh vignette while preserving authentic studio color, lighting, and texture.
    Composites the crisp foreground back onto the smoothed, cleaned backdrop.
    """
    h, w = img_bgr.shape[:2]
    if len(alpha_mask.shape) == 3:
        alpha_mask = cv2.cvtColor(alpha_mask, cv2.COLOR_BGR2GRAY)

    alpha_norm = (alpha_mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
    bg_weight = 1.0 - alpha_norm

    # Large spatial smoothing kernel proportional to image size (e.g. 4% of width, min 31)
    ksize = int(max(31, (w // 25) | 1))

    # Boundary-aware normalized convolution to smooth out creases & blotches without subject bleed
    bg_raw = img_bgr.astype(np.float32) * bg_weight
    bg_weight_blurred = cv2.GaussianBlur(bg_weight[:, :, 0], (ksize, ksize), 0)[:, :, np.newaxis]
    bg_weight_blurred = np.maximum(bg_weight_blurred, 1e-4)

    bg_blurred = cv2.GaussianBlur(bg_raw, (ksize, ksize), 0) / bg_weight_blurred

    # Subtle film grain to prevent banding
    np.random.seed(42)
    noise = np.random.normal(0, 0.7, (h, w, 3)).astype(np.float32)
    cleaned_bg = np.clip(bg_blurred + noise, 0.0, 255.0).astype(np.uint8)

    # Composite subject onto the cleaned background
    return composite_subject_onto_backdrop(img_bgr, alpha_mask, cleaned_bg, decontaminate=False)


def generate_studio_backdrop(
    width: int,
    height: int,
    backdrop_type: str = "classic_blue",
    face_info: Optional[Dict[str, Any]] = None,
    custom_img_bgr: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Renders high-resolution authentic studio backdrops with smooth radial gradients,
    strobe spotlight dynamically positioned behind the detected head, and fine grain.
    """
    if backdrop_type == "custom" and custom_img_bgr is not None:
        return cv2.resize(custom_img_bgr, (width, height), interpolation=cv2.INTER_LANCZOS4)

    # Resolve aliases
    resolved_type = BACKDROP_ALIASES.get(backdrop_type, backdrop_type)
    info = STUDIO_BACKDROPS.get(resolved_type, STUDIO_BACKDROPS.get(backdrop_type, STUDIO_BACKDROPS["classic_blue"]))

    # Check pre-rendered disk asset if available
    if info.get("file") and os.path.exists(info["file"]):
        loaded_bg = cv2.imread(info["file"])
        if loaded_bg is not None:
            return cv2.resize(loaded_bg, (width, height), interpolation=cv2.INTER_LANCZOS4)

    # Dynamic Spotlight Synthesis
    # Size and position the light spot from detected face coordinates
    if face_info and 'bbox' in face_info:
        fx, fy, fw, fh = face_info['bbox']
        cx = float(fx + fw / 2.0)
        cy = float(fy + fh * 0.40)  # Behind upper face / head
        rx = max(float(fw) * 2.4, float(width) * 0.45)
        ry = max(float(fh) * 2.4, float(height) * 0.45)
    else:
        cx = float(width / 2.0)
        cy = float(height * 0.38)
        rx = float(width * 0.50)
        ry = float(height * 0.50)

    y, x = np.ogrid[:height, :width]
    dist = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
    dist = np.clip(dist, 0.0, 1.0)

    # Smoothstep interpolation (cubic Hermite) for banding-free soft falloff
    s = dist * dist * (3.0 - 2.0 * dist)

    spot_bgr = np.array(info.get("spot_bgr", (144, 84, 43)), dtype=np.float32)
    outer_bgr = np.array(info.get("outer_bgr", (48, 28, 15)), dtype=np.float32)

    grad = spot_bgr * (1.0 - s[:, :, np.newaxis]) + outer_bgr * s[:, :, np.newaxis]

    # Very fine dither grain to prevent 8-bit quantization banding
    np.random.seed(42)
    noise = np.random.normal(0.0, 0.8, (height, width, 3)).astype(np.float32)
    bg = np.clip(grad + noise, 0.0, 255.0).astype(np.uint8)
    return bg


def composite_subject_onto_backdrop(
    subject_bgr: np.ndarray,
    alpha_mask: np.ndarray,
    backdrop_bgr: np.ndarray,
    edge_feather_px: int = 0,
    decontaminate: bool = True
) -> np.ndarray:
    """
    Composites foreground subject onto the studio backdrop with:
      1. Edge color decontamination (removes old background color bleed/fringe).
      2. Contact shadow and matched edge blur to eliminate the 'pasted on' look.
      3. Fractional alpha blending preserving hair strands, tassels, and cap.
    """
    h, w = subject_bgr.shape[:2]
    bg_resized = cv2.resize(backdrop_bgr, (w, h), interpolation=cv2.INTER_LANCZOS4)

    if len(alpha_mask.shape) == 3:
        alpha_mask = cv2.cvtColor(alpha_mask, cv2.COLOR_BGR2GRAY)

    if edge_feather_px > 0:
        kernel_size = edge_feather_px * 2 + 1
        alpha_feathered = cv2.GaussianBlur(alpha_mask, (kernel_size, kernel_size), 0)
    else:
        alpha_feathered = alpha_mask

    # 1. Edge Color Decontamination
    if decontaminate:
        subject_clean = decontaminate_edges(subject_bgr, alpha_feathered)
    else:
        subject_clean = subject_bgr

    alpha_norm = (alpha_feathered.astype(np.float32) / 255.0)[:, :, np.newaxis]
    subj_f = subject_clean.astype(np.float32)
    bg_f = bg_resized.astype(np.float32)

    # 2. Subtle Contact Shadow: soft shadow cast onto the backdrop behind subject
    shadow_blur = cv2.GaussianBlur(alpha_norm[:, :, 0], (31, 31), 0)
    # Slight downward shift (6px down, 2px right)
    M = np.float32([[1, 0, 2], [0, 1, 6]])
    shadow_shifted = cv2.warpAffine(shadow_blur, M, (w, h), borderMode=cv2.BORDER_CONSTANT, borderValue=0)[:, :, np.newaxis]
    # Subtle 12% darkening only on the backdrop zone outside the subject
    bg_with_shadow = bg_f * (1.0 - 0.12 * shadow_shifted * (1.0 - alpha_norm))

    # 3. Seamless fractional alpha composite
    composited = subj_f * alpha_norm + bg_with_shadow * (1.0 - alpha_norm)
    return np.clip(composited, 0.0, 255.0).astype(np.uint8)
