"""
KameraPh AI Beautification & High-End Studio Portrait Engine
------------------------------------------------------------
Implements natural, publication-grade portrait retouching with semantic face parsing:
  - Exact semantic parsing masks (skin, hair, eyes, brows, lips, neck, hat, cloth)
  - Frequency separation with pore preservation (no plastic look)
  - Black-hat blemish & acne removal with 'keep moles' preservation
  - Even skin tone & blotch/redness correction (without altering natural melanin)
  - Loose hair cleanup: flyaway hair alpha smoothing & facial stray hair inpainting
  - Refined eye clarity: subtle iris brightening and limbal sharpening (no white rings)
  - Natural lip enhancement (clarity & natural sheen, color tint off by default)
  - Soft highlight bloom on skin highlights only
  - Expensive studio lighting: key light, alpha rim light, S-curve contrast
  - Cap & gown clarity with highlight recovery for bright white gowns
  - 3 Photographer Presets: Natural, Studio Glow, Yearbook Classic
"""

import os
import cv2
import numpy as np
from typing import Dict, Any, Optional, Tuple, Union
from face_parsing import get_face_parsing_masks

BEAUTY_PRESETS = {
    "natural": {
        "id": "natural",
        "name": "Natural Clean",
        "description": "Authentic clean graduation portrait. Natural skin texture, authentic pores, zero plastic smoothing, and subtle eye clarity.",
        "skin_smoothing": 0.45,
        "blemish_cut": 0.50,
        "spot_correction": 0.35,
        "keep_moles": True,
        "loose_hair_cleanup": 0.30,
        "cleanup_loose_hair": True,
        "shine_reduction": 0.25,
        "lip_intensity": 0.0,
        "lip_enhancement": 0.25,
        "eye_sharpen": 0.15,
        "eye_catchlight": 0.15,
        "glow_intensity": 0.15,
        "studio_light_intensity": 0.12,
        "rim_light_boost": 0.10,
        "highlight_recovery": 0.50,
        "lighting_temp": "neutral_5500k",
        "fidelity_weight": 0.85
    },
    "studio_glow": {
        "id": "studio_glow",
        "name": "Studio Glow",
        "description": "Flattering soft key-light bloom, delicate cheekbone glow, polished blemish correction, and subtle eye brightness.",
        "skin_smoothing": 0.60,
        "blemish_cut": 0.65,
        "spot_correction": 0.45,
        "keep_moles": True,
        "loose_hair_cleanup": 0.50,
        "cleanup_loose_hair": True,
        "shine_reduction": 0.35,
        "lip_intensity": 0.0,
        "lip_enhancement": 0.35,
        "eye_sharpen": 0.22,
        "eye_catchlight": 0.22,
        "glow_intensity": 0.30,
        "studio_light_intensity": 0.22,
        "rim_light_boost": 0.20,
        "highlight_recovery": 0.60,
        "lighting_temp": "neutral_5500k",
        "fidelity_weight": 0.75
    },
    "yearbook_classic": {
        "id": "yearbook_classic",
        "name": "Yearbook Classic",
        "description": "Formal studio contrast, balanced rich tones, crisp mortarboard and toga definition, and clean print highlights.",
        "skin_smoothing": 0.55,
        "blemish_cut": 0.60,
        "spot_correction": 0.40,
        "keep_moles": True,
        "loose_hair_cleanup": 0.40,
        "cleanup_loose_hair": True,
        "shine_reduction": 0.30,
        "lip_intensity": 0.0,
        "lip_enhancement": 0.30,
        "eye_sharpen": 0.28,
        "eye_catchlight": 0.25,
        "glow_intensity": 0.20,
        "studio_light_intensity": 0.25,
        "rim_light_boost": 0.18,
        "highlight_recovery": 0.70,
        "lighting_temp": "neutral_5500k",
        "fidelity_weight": 0.80
    }
}

# Aliases for backward compatibility
PRESET_ALIASES = {
    "morena_radiant": "studio_glow",
    "natural_clean": "natural",
    "studio_glamour": "studio_glow",
    "high_key_crisp": "yearbook_classic"
}

LIP_COLOR_PALETTES = {
    "natural_rose": {"id": "natural_rose", "name": "Natural Rose", "hex": "#d87093", "rgb": (216, 112, 147)},
    "coral_peach": {"id": "coral_peach", "name": "Coral Peach", "hex": "#e07a5f", "rgb": (224, 122, 95)},
    "berry_plum": {"id": "berry_plum", "name": "Berry Plum", "hex": "#c71585", "rgb": (199, 21, 133)},
    "crimson_ruby": {"id": "crimson_ruby", "name": "Crimson Ruby", "hex": "#b22222", "rgb": (178, 34, 34)},
    "nude_cherry": {"id": "nude_cherry", "name": "Nude Cherry", "hex": "#c97a7e", "rgb": (201, 122, 126)},
    "warm_terracotta": {"id": "warm_terracotta", "name": "Warm Terracotta", "hex": "#c45b43", "rgb": (196, 91, 67)}
}


def hex_to_bgr(hex_code: str) -> Tuple[int, int, int]:
    """Converts hex color string to BGR tuple."""
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return (b, g, r)
    return (147, 112, 216)


def detect_and_heal_blemishes(
    img_bgr: np.ndarray,
    skin_mask: np.ndarray,
    blemish_strength: float = 0.60,
    keep_moles: bool = True
) -> np.ndarray:
    """
    Detects small dark spots and acne inside the skin mask using Black-Hat transform on
    the L* channel of CIELAB, filtered by size and contrast, and inpaints them.
    Preserves authentic beauty marks and moles by filtering out high-contrast, compact spots.
    """
    if blemish_strength <= 0.05 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_bgr

    ys, xs = np.where(skin_mask > 0)
    if len(ys) == 0:
        return img_bgr
    y1, y2 = max(0, int(ys.min()) - 10), min(img_bgr.shape[0], int(ys.max()) + 10)
    x1, x2 = max(0, int(xs.min()) - 10), min(img_bgr.shape[1], int(xs.max()) + 10)

    roi_img = img_bgr[y1:y2, x1:x2]
    roi_mask = skin_mask[y1:y2, x1:x2]

    lab = cv2.cvtColor(roi_img, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]

    # Black-hat transform isolates structures darker than surrounding skin
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
    blackhat = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, kernel)

    thresh_val = int(max(6, 16 - blemish_strength * 8))
    _, raw_spots = cv2.threshold(blackhat, thresh_val, 255, cv2.THRESH_BINARY)
    raw_spots = cv2.bitwise_and(raw_spots, roi_mask)

    # Connected components analysis to filter by spot size (2 to 14 px radius) and keep moles
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(raw_spots, connectivity=8)
    heal_mask = np.zeros_like(raw_spots)

    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < 3 or area > 220:
            continue

        spot_comp = (labels == i)
        spot_contrast = float(np.mean(blackhat[spot_comp]))

        # Keep moles: moles have very dark uniform pigmentation and sharp border gradient
        is_mole = False
        if keep_moles and area <= 80:
            w_box = stats[i, cv2.CC_STAT_WIDTH]
            h_box = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = float(w_box) / max(float(h_box), 1.0)
            if 0.7 <= aspect <= 1.4 and spot_contrast > 28.0:
                is_mole = True

        if not is_mole:
            heal_mask[spot_comp] = 255

    if cv2.countNonZero(heal_mask) > 0:
        heal_mask_dilated = cv2.dilate(heal_mask, np.ones((3, 3), np.uint8), iterations=1)
        inpainted = cv2.inpaint(roi_img, heal_mask_dilated, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        alpha_heal = (cv2.GaussianBlur(heal_mask_dilated, (3, 3), 0).astype(np.float32) / 255.0 * blemish_strength)[:, :, None]
        roi_healed = inpainted.astype(np.float32) * alpha_heal + roi_img.astype(np.float32) * (1.0 - alpha_heal)
        out = img_bgr.copy()
        out[y1:y2, x1:x2] = np.clip(roi_healed, 0, 255).astype(np.uint8)
        return out

    return img_bgr


def correct_spots_and_even_skin_tone(
    img_bgr: np.ndarray,
    skin_mask: np.ndarray,
    spot_correction: float = 0.50,
    eyes_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Evens out blotches, hyperpigmentation, redness, and under-eye dark circles
    inside the skin mask without altering or bleaching the student's authentic Morena skin tone.
    Simulates high-end liquid foundation and under-eye concealer application.
    """
    if spot_correction <= 0.05 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_bgr

    h, w = img_bgr.shape[:2]
    scale_ref = float(np.clip(max(h, w) / 1000.0, 0.4, 6.0))

    ys, xs = np.where(skin_mask > 0)
    if len(ys) == 0:
        return img_bgr
    margin = int(15 * scale_ref)
    y1, y2 = max(0, int(ys.min()) - margin), min(h, int(ys.max()) + margin)
    x1, x2 = max(0, int(xs.min()) - margin), min(w, int(xs.max()) + margin)

    roi_bgr = img_bgr[y1:y2, x1:x2]
    roi_mask = skin_mask[y1:y2, x1:x2]

    roi_lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    # Resolution-adaptive local median skin luminance and chrominance
    k_med = 2 * int(12 * scale_ref) + 1
    max_k = (min(y2 - y1, x2 - x1) // 2) * 2 - 1
    if max_k >= 3:
        k_med = min(k_med, max_k)
    else:
        k_med = 3

    median_bgr = cv2.medianBlur(roi_bgr, k_med)
    median_lab = cv2.cvtColor(median_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    skin_f = (roi_mask.astype(np.float32) / 255.0)

    # 1. Foundation Tone Evening: gently reduce dark blotches towards local median
    dark_deficit = np.maximum(0.0, median_lab[:, :, 0] - roi_lab[:, :, 0])
    roi_lab[:, :, 0] += dark_deficit * (spot_correction * 0.42) * skin_f

    # 2. Color-Correcting Primer: reduce blotchy redness (a* deviations) towards local median
    a_diff = roi_lab[:, :, 1] - median_lab[:, :, 1]
    red_blotch = np.maximum(0.0, a_diff)
    roi_lab[:, :, 1] -= red_blotch * (spot_correction * 0.45) * skin_f

    # 3. Under-Eye Concealer: lift under-eye hollows and correct bluish/purple shadow cast
    if eyes_mask is not None and cv2.countNonZero(eyes_mask) > 0:
        roi_eyes = eyes_mask[y1:y2, x1:x2]
        if cv2.countNonZero(roi_eyes) > 0:
            e_ys, e_xs = np.where(roi_eyes > 0)
            eye_h = int(e_ys.max() - e_ys.min())
            ue_y1 = int(e_ys.max())
            ue_y2 = min(roi_bgr.shape[0], ue_y1 + int(eye_h * 0.75))
            ue_x1 = max(0, int(e_xs.min()) - int(10 * scale_ref))
            ue_x2 = min(roi_bgr.shape[1], int(e_xs.max()) + int(10 * scale_ref))

            ue_mask = np.zeros(roi_mask.shape, dtype=np.float32)
            ue_mask[ue_y1:ue_y2, ue_x1:ue_x2] = (roi_mask[ue_y1:ue_y2, ue_x1:ue_x2] > 0).astype(np.float32)
            k_blur = 2 * int(5 * scale_ref) + 1
            ue_mask = cv2.GaussianBlur(ue_mask, (k_blur, k_blur), 0)

            # Concealer: gently brighten dark eye hollows and harmonize coolness
            ue_dark = np.maximum(0.0, median_lab[:, :, 0] - roi_lab[:, :, 0])
            roi_lab[:, :, 0] += ue_dark * (spot_correction * 0.35) * ue_mask
            b_diff = np.maximum(0.0, median_lab[:, :, 2] - roi_lab[:, :, 2])
            roi_lab[:, :, 2] += b_diff * (spot_correction * 0.25) * ue_mask

    out = img_bgr.copy()
    out[y1:y2, x1:x2] = cv2.cvtColor(np.clip(roi_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return out


def whiten_dark_spots_and_hyperpigmentation(img_bgr, skin_mask, whitening_strength=0.50):
    """Backward compatibility wrapper for spot_correction."""
    return correct_spots_and_even_skin_tone(img_bgr, skin_mask, spot_correction=whitening_strength)


def apply_ultra_makeup_skin_smoothing(
    img_f: np.ndarray,
    skin_mask: np.ndarray,
    skin_smoothing: float = 0.50,
    shine_reduction: float = 0.30,
    eyes_mask: Optional[np.ndarray] = None,
    brows_mask: Optional[np.ndarray] = None,
    lips_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Ultra-realistic, professional makeup artist skin finish:
    1. Multi-band frequency separation (Low = bone structure & 3D contours,
       Mid = foundation/primer smoothing, High = crisp micro-pores & velvet skin grain).
    2. Soft-knee spike compression on high frequency to remove harsh dry flakes and acne pits
       while preserving 100% of authentic organic skin pores and micro-texture.
    3. Translucent setting powder diffusion for oily T-zone (diffuses harsh glare into satin matte,
       never darkening into muddy gray).
    4. Anatomical feature isolation: eyes, brows, and lips masks are feathered and strictly protected
       to prevent any softening of eyelashes, eyebrows, or lip contours.
    """
    if skin_smoothing <= 0.05 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_f

    h, w = img_f.shape[:2]
    scale_ref = float(np.clip(max(h, w) / 1000.0, 0.4, 6.0))

    # 1. Feature protection: strictly protect eyes, brows, and lips
    protected_mask = np.zeros((h, w), dtype=np.uint8)
    for m in [eyes_mask, brows_mask, lips_mask]:
        if m is not None and cv2.countNonZero(m) > 0:
            protected_mask = cv2.bitwise_or(protected_mask, m)

    protect_radius = max(3, int(4 * scale_ref))
    protect_dilated = cv2.dilate(
        protected_mask,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (protect_radius, protect_radius)),
        iterations=1
    )
    clean_skin = cv2.bitwise_and(skin_mask, cv2.bitwise_not(protect_dilated))

    k_feather = 2 * int(4 * scale_ref) + 1
    skin_mask_f = (cv2.GaussianBlur(clean_skin, (k_feather, k_feather), 0).astype(np.float32) / 255.0)[:, :, None]

    # 2. Multi-Band Decomposition
    k_low = 2 * int(14 * scale_ref) + 1
    k_mid = 2 * int(4 * scale_ref) + 1

    low_base = cv2.GaussianBlur(img_f, (k_low, k_low), 0)
    low_mid = cv2.GaussianBlur(img_f, (k_mid, k_mid), 0)

    high_raw = img_f - low_mid
    mid_raw = low_mid - low_base

    # 3. Foundation Canvas Smoothing on Mid Frequencies (Edge-preserving bilateral filter)
    d_bi = 2 * int(5 * scale_ref) + 1
    sig_col = 24.0
    sig_sp = 8.0 * scale_ref

    low_mid_u8 = np.clip(low_mid, 0, 255).astype(np.uint8)
    smoothed_mid_u8 = cv2.bilateralFilter(low_mid_u8, d=d_bi, sigmaColor=sig_col, sigmaSpace=sig_sp)
    smoothed_mid_f = smoothed_mid_u8.astype(np.float32)

    mid_smooth = smoothed_mid_f - low_base
    mid_blended = mid_raw * (1.0 - skin_smoothing) + mid_smooth * skin_smoothing

    # 4. Velvet Micro-Pore Regularization (High Frequency)
    # Soft-knee compression of harsh spikes (flaky skin, deep pore pits), preserving crisp pores
    high_mag = np.abs(high_raw)
    threshold_spike = 13.0 * scale_ref
    high_refined = np.where(
        high_mag > threshold_spike,
        np.sign(high_raw) * (threshold_spike + (high_mag - threshold_spike) * 0.35),
        high_raw * (1.0 + skin_smoothing * 0.12)  # subtle micro-pore clarity boost for velvet finish
    )

    recombined = low_base + mid_blended + high_refined

    # 5. Translucent Setting Powder Satin Matte De-Shine
    if shine_reduction > 0.05:
        gray = cv2.cvtColor(np.clip(img_f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        shine_pts = np.clip((gray - 180.0) / 70.0, 0.0, 1.0)
        k_shine = 2 * int(6 * scale_ref) + 1
        shine_blur = cv2.GaussianBlur(shine_pts, (k_shine, k_shine), 0)
        shine_factor = shine_blur * skin_mask_f[:, :, 0] * (shine_reduction * 0.65)

        # Satin diffusion target: rolls off specular peak into soft, glowing skin tone
        satin_target = recombined * 0.65 + low_base * 0.35
        recombined = recombined * (1.0 - shine_factor[:, :, None]) + satin_target * shine_factor[:, :, None]

    out = recombined * skin_mask_f + img_f * (1.0 - skin_mask_f)
    return np.clip(out, 0, 255)


def cleanup_facial_stray_hairs(
    img_bgr: np.ndarray,
    skin_mask: np.ndarray,
    strength: float = 0.50
) -> np.ndarray:
    """
    Detects thin dark stray hair strands across forehead and cheeks inside the skin mask
    using directional line filters and inpaints them.
    """
    if strength <= 0.05 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_bgr

    ys, xs = np.where(skin_mask > 0)
    if len(ys) == 0:
        return img_bgr
    y1, y2 = max(0, int(ys.min()) - 10), min(img_bgr.shape[0], int(ys.max()) + 10)
    x1, x2 = max(0, int(xs.min()) - 10), min(img_bgr.shape[1], int(xs.max()) + 10)

    roi_img = img_bgr[y1:y2, x1:x2]
    roi_mask = skin_mask[y1:y2, x1:x2]

    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    stray_mask = np.zeros_like(gray)
    k_sizes = [(1, 9), (9, 1), (5, 5), (7, 3)]
    for (kh, kw) in k_sizes:
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh))
        bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, k)
        _, thresh = cv2.threshold(bh, 14, 255, cv2.THRESH_BINARY)
        stray_mask = cv2.bitwise_or(stray_mask, thresh)

    stray_mask = cv2.bitwise_and(stray_mask, roi_mask)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(stray_mask, connectivity=8)
    final_stray = np.zeros_like(gray)
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        w_box = stats[i, cv2.CC_STAT_WIDTH]
        h_box = stats[i, cv2.CC_STAT_HEIGHT]
        if 4 <= area <= 220 and (w_box >= h_box * 1.6 or h_box >= w_box * 1.6):
            final_stray[labels == i] = 255

    if cv2.countNonZero(final_stray) > 0:
        inpaint_mask = cv2.dilate(final_stray, np.ones((3, 3), np.uint8), iterations=1)
        inpainted = cv2.inpaint(roi_img, inpaint_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        alpha = (final_stray.astype(np.float32) / 255.0 * strength)[:, :, None]
        roi_cleaned = np.clip(inpainted.astype(np.float32) * alpha + roi_img.astype(np.float32) * (1.0 - alpha), 0, 255).astype(np.uint8)
        out = img_bgr.copy()
        out[y1:y2, x1:x2] = roi_cleaned
        return out

    return img_bgr


def cleanup_flyaway_hair_alpha(
    alpha_mask: np.ndarray,
    hair_mask: Optional[np.ndarray] = None,
    strength: float = 0.50
) -> np.ndarray:
    """Smooths outer hair silhouette and removes thin flyaway strands sticking out into backdrop."""
    if strength <= 0.05 or alpha_mask is None:
        return alpha_mask

    ksize = int(max(3, round(strength * 5) | 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))

    h, w = alpha_mask.shape[:2]
    hair_zone = np.zeros_like(alpha_mask)
    hair_zone[:int(h * 0.55), :] = 255
    if hair_mask is not None and cv2.countNonZero(hair_mask) > 0:
        hair_zone = cv2.dilate(hair_mask, np.ones((15, 15), np.uint8), iterations=2)

    smoothed_alpha = cv2.morphologyEx(alpha_mask, cv2.MORPH_OPEN, kernel)
    weight = (cv2.GaussianBlur(hair_zone, (15, 15), 0).astype(np.float32) / 255.0) * strength
    res = alpha_mask.astype(np.float32) * (1.0 - weight) + smoothed_alpha.astype(np.float32) * weight
    return np.clip(res, 0, 255).astype(np.uint8)


def enhance_eyes_refined(
    img_f: np.ndarray,
    eyes_mask: np.ndarray,
    eye_sharpen: float = 0.20,
    catchlight_boost: float = 0.20
) -> np.ndarray:
    """Refined eye enhancement strictly inside the semantic eye mask without artificial white rings."""
    if eyes_mask is None or cv2.countNonZero(eyes_mask) == 0:
        return img_f

    ys, xs = np.where(eyes_mask > 0)
    if len(ys) == 0:
        return img_f
    y1, y2 = max(0, int(ys.min()) - 10), min(img_f.shape[0], int(ys.max()) + 10)
    x1, x2 = max(0, int(xs.min()) - 10), min(img_f.shape[1], int(xs.max()) + 10)

    roi_f = img_f[y1:y2, x1:x2]
    roi_mask = eyes_mask[y1:y2, x1:x2]

    roi_hsv = cv2.cvtColor(np.clip(roi_f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    v = roi_hsv[:, :, 2]

    # Sclera / eye whites: very subtle lift (max 4%), no harsh desaturation
    sclera = (roi_mask > 50) & (v > 130)
    roi_hsv[:, :, 2] = np.where(sclera, np.clip(v * 1.04, 0, 255), v)

    # Specular catchlight: gentle glint enhancement, strictly inside pupil/iris
    if catchlight_boost > 0.05:
        glint = (roi_mask > 50) & (v > 190)
        roi_hsv[:, :, 2] = np.where(glint, np.clip(v + catchlight_boost * 18.0, 0, 255), v)

    enhanced = cv2.cvtColor(np.clip(roi_hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    if eye_sharpen > 0.05:
        blurred = cv2.GaussianBlur(enhanced, (0, 0), 1.5)
        sharpened = cv2.addWeighted(enhanced, 1.0 + eye_sharpen * 0.4, blurred, -eye_sharpen * 0.4, 0)
        mask_f = (cv2.GaussianBlur(roi_mask, (5, 5), 0).astype(np.float32) / 255.0)[:, :, None]
        roi_out = roi_f * (1.0 - mask_f) + sharpened * mask_f
    else:
        mask_f = (roi_mask.astype(np.float32) / 255.0)[:, :, None]
        roi_out = roi_f * (1.0 - mask_f) + enhanced * mask_f

    out = img_f.copy()
    out[y1:y2, x1:x2] = roi_out
    return out


def enhance_eye_catchlights(img_f, r_eye, l_eye, fw, eye_sharpen=0.20, catchlight_boost=0.20):
    """Backward compatibility wrapper creating landmark eye mask."""
    h, w = img_f.shape[:2]
    eye_mask = np.zeros((h, w), dtype=np.uint8)
    for (ex, ey) in [r_eye, l_eye]:
        cv2.circle(eye_mask, (int(ex), int(ey)), int(fw * 0.10), 255, -1)
    return enhance_eyes_refined(img_f, eye_mask, eye_sharpen=eye_sharpen, catchlight_boost=catchlight_boost)


def enhance_lips_natural(
    img_f: np.ndarray,
    lips_mask: np.ndarray,
    lip_enhancement: float = 0.30,
    lip_color_hex: Optional[str] = None,
    lip_intensity: float = 0.0
) -> np.ndarray:
    """Natural lip enhancement strictly inside semantic lip mask (color tint off by default)."""
    if lips_mask is None or cv2.countNonZero(lips_mask) == 0:
        return img_f

    ys, xs = np.where(lips_mask > 0)
    if len(ys) == 0:
        return img_f
    y1, y2 = max(0, int(ys.min()) - 10), min(img_f.shape[0], int(ys.max()) + 10)
    x1, x2 = max(0, int(xs.min()) - 10), min(img_f.shape[1], int(xs.max()) + 10)

    roi_f = img_f[y1:y2, x1:x2]
    roi_mask = lips_mask[y1:y2, x1:x2]

    hsv = cv2.cvtColor(np.clip(roi_f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    if lip_enhancement > 0.05:
        mask_bool = roi_mask > 50
        hsv[:, :, 1] = np.where(mask_bool, np.clip(hsv[:, :, 1] * (1.0 + lip_enhancement * 0.22), 0, 255), hsv[:, :, 1])

    enhanced = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    if lip_intensity > 0.05 and lip_color_hex:
        tint_bgr = np.array(hex_to_bgr(lip_color_hex), dtype=np.float32)
        p_norm = enhanced / 255.0
        t_norm = tint_bgr / 255.0
        soft_light = (1.0 - 2.0 * t_norm) * (p_norm ** 2) + 2.0 * t_norm * p_norm
        tinted = np.clip(soft_light * 255.0, 0, 255)
        enhanced = enhanced * (1.0 - lip_intensity) + tinted * lip_intensity

    mask_f = (cv2.GaussianBlur(roi_mask, (5, 5), 0).astype(np.float32) / 255.0)[:, :, None]
    roi_out = roi_f * (1.0 - mask_f) + enhanced * mask_f

    out = img_f.copy()
    out[y1:y2, x1:x2] = roi_out
    return out


def recolor_lips_neural(img_f, r_mouth, l_mouth, fw, fh, lip_color_hex="#d87093", lip_intensity=0.0):
    """Backward compatibility wrapper for lips."""
    h, w = img_f.shape[:2]
    mouth_cx = (int(r_mouth[0]) + int(l_mouth[0])) // 2
    mouth_cy = (int(r_mouth[1]) + int(l_mouth[1])) // 2
    lip_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(lip_mask, (int(mouth_cx), int(mouth_cy)), (max(1, int(fw * 0.22)), max(1, int(fh * 0.10))), 0, 0, 360, 255, -1)
    return enhance_lips_natural(img_f, lip_mask, lip_enhancement=0.30, lip_color_hex=lip_color_hex, lip_intensity=lip_intensity)


def apply_subsurface_melanin_radiance(img_f, skin_mask_f, glow_intensity=0.25, is_morena=True):
    """Soft, low-strength highlight bloom on skin highlights only."""
    if glow_intensity <= 0.05 or skin_mask_f is None:
        return img_f

    gray = cv2.cvtColor(np.clip(img_f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    highlight_mask = np.clip((gray - 135.0) / 95.0, 0.0, 1.0)[:, :, np.newaxis]

    bloom = cv2.GaussianBlur(img_f, (27, 27), 0)
    if is_morena:
        bloom[:, :, 2] = np.clip(bloom[:, :, 2] * 1.025, 0, 255)
        bloom[:, :, 1] = np.clip(bloom[:, :, 1] * 1.012, 0, 255)

    glow_factor = glow_intensity * 0.22 * skin_mask_f * highlight_mask
    out = img_f * (1.0 - glow_factor) + (img_f + bloom * 0.35) * glow_factor
    return np.clip(out, 0, 255)


def enhance_clothing_and_regalia(
    img_f: np.ndarray,
    hat_mask: Optional[np.ndarray],
    cloth_mask: Optional[np.ndarray],
    clarity_strength: float = 0.35,
    highlight_recovery: float = 0.60
) -> np.ndarray:
    """Enhances graduation regalia: micro-contrast on cap/gown and highlight recovery on white gowns."""
    h, w = img_f.shape[:2]
    regalia_mask = np.zeros((h, w), dtype=np.uint8)
    if hat_mask is not None:
        regalia_mask = cv2.bitwise_or(regalia_mask, hat_mask)
    if cloth_mask is not None:
        regalia_mask = cv2.bitwise_or(regalia_mask, cloth_mask)

    if cv2.countNonZero(regalia_mask) == 0:
        return img_f

    out = img_f.copy()

    # Highlight recovery on white gown / cap highlights (> 225)
    if highlight_recovery > 0.05:
        gray = cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
        hi_zone = (regalia_mask > 50) & (gray > 225.0)
        if np.any(hi_zone):
            excess = np.maximum(0.0, gray - 225.0)[:, :, None]
            out = np.where(hi_zone[:, :, None], out - excess * (highlight_recovery * 0.35), out)

    # Texture clarity on cap and gown
    if clarity_strength > 0.05:
        blurred = cv2.GaussianBlur(out, (0, 0), 2.5)
        clarity_boost = cv2.addWeighted(out, 1.0 + clarity_strength * 0.45, blurred, -clarity_strength * 0.45, 0)
        mask_f = (cv2.GaussianBlur(regalia_mask, (7, 7), 0).astype(np.float32) / 255.0)[:, :, None]
        out = out * (1.0 - mask_f) + clarity_boost * mask_f

    return np.clip(out, 0, 255)


def apply_studio_environment_lighting(
    img_f: np.ndarray,
    subject_mask: Optional[np.ndarray] = None,
    lighting_temp: str = "neutral_5500k",
    studio_light_intensity: float = 0.20,
    rim_light_boost: float = 0.20,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """Applies professional three-point studio lighting: soft key light, rim light, and gentle S-curve."""
    h, w = img_f.shape[:2]
    out = img_f.copy()

    # 1. Soft Key Light from face position
    if studio_light_intensity > 0.05 and face_info and 'bbox' in face_info:
        fx, fy, fw, fh = face_info['bbox']
        kx = float(fx - fw * 0.3)
        ky = float(fy - fh * 0.3)
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt(((x - kx) / (w * 0.75)) ** 2 + ((y - ky) / (h * 0.75)) ** 2)
        key_gradient = np.clip(1.0 - dist, 0.0, 1.0)[:, :, None]
        out += out * (key_gradient * studio_light_intensity * 0.20)

    # 2. Subtle Rim Light along alpha boundary
    if rim_light_boost > 0.05 and subject_mask is not None:
        if len(subject_mask.shape) == 3:
            s_mask = cv2.cvtColor(subject_mask, cv2.COLOR_BGR2GRAY)
        else:
            s_mask = subject_mask
        edges = cv2.Canny(s_mask, 80, 180)
        rim = cv2.dilate(edges, np.ones((5, 5), np.uint8), iterations=1)
        rim_blur = (cv2.GaussianBlur(rim, (7, 7), 0).astype(np.float32) / 255.0)[:, :, None]
        out += rim_blur * (rim_light_boost * 35.0)

    # 3. Gentle S-Curve for contrast
    norm = out / 255.0
    s_curve = norm * norm * (3.0 - 2.0 * norm)
    out = (norm * 0.90 + s_curve * 0.10) * 255.0

    return np.clip(out, 0, 255)


def apply_beauty_preset_to_image(
    img_bgr: np.ndarray,
    face_info: Optional[Dict[str, Any]] = None,
    preset_id: str = "natural",
    custom_adjustments: Optional[Dict[str, Any]] = None,
    ai_config: Optional[Dict[str, Any]] = None,
    precomputed_masks: Optional[Dict[str, np.ndarray]] = None,
    subject_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Main entry point for high-end studio portrait beautification.
    Uses semantic face parsing masks to apply pore-preserving skin smoothing,
    blemish healing (preserving moles), even skin tones, loose hair cleanup,
    refined eye clarity, natural lip enhancement, and studio regalia lighting.
    """
    # Resolve preset
    resolved_id = PRESET_ALIASES.get(preset_id, preset_id)
    preset_dict = BEAUTY_PRESETS.get(resolved_id, BEAUTY_PRESETS["natural"]).copy()
    if custom_adjustments:
        preset_dict.update(custom_adjustments)

    h, w = img_bgr.shape[:2]
    img_f = img_bgr.astype(np.float32)

    if face_info is None or 'bbox' not in face_info:
        # Fallback to general studio environment lighting without facial retouching
        lit = apply_studio_environment_lighting(img_f, studio_light_intensity=0.15)
        # Apply Aftershoot-style color profile grading even when face landmarks are absent
        color_profile_id = preset_dict.get("color_profile", "clean_commercial")
        color_warmth = float(preset_dict.get("color_warmth", 0.0))
        color_contrast = float(preset_dict.get("color_contrast", 0.0))
        color_vibrance = float(preset_dict.get("color_vibrance", 0.0))
        final = apply_aftershoot_color_grading(
            lit,
            profile_id=color_profile_id,
            warmth=color_warmth,
            contrast=color_contrast,
            vibrance=color_vibrance
        )
        return np.clip(final, 0, 255).astype(np.uint8)

    # 1. Semantic Face Parsing Masks
    if precomputed_masks:
        masks = precomputed_masks
    else:
        masks = get_face_parsing_masks(img_bgr, face_info)
    skin_mask = masks["skin"]
    eyes_mask = masks["eyes"]
    lips_mask = masks["lips"]
    hat_mask = masks["hat"]
    cloth_mask = masks["cloth"]

    # 2. Stray hair cleanup on face and forehead
    cleanup_hair = preset_dict.get("cleanup_loose_hair", True)
    hair_strength = float(preset_dict.get("loose_hair_cleanup", 0.40))
    if cleanup_hair and hair_strength > 0.05:
        img_bgr = cleanup_facial_stray_hairs(img_bgr, skin_mask, strength=hair_strength)

    # 3. Blemish & Acne Removal (with Keep Moles option)
    blemish_cut = float(preset_dict.get("blemish_cut", 0.60))
    keep_moles = bool(preset_dict.get("keep_moles", True))
    healed_bgr = detect_and_heal_blemishes(img_bgr, skin_mask, blemish_strength=blemish_cut, keep_moles=keep_moles)

    # 4. Spot Correction & Even Skin Tone (Redness/blotch balancing)
    spot_correction = float(preset_dict.get("spot_correction", preset_dict.get("dark_spot_whitening", 0.40)))
    healed_bgr = correct_spots_and_even_skin_tone(healed_bgr, skin_mask, spot_correction=spot_correction)
    healed_f = healed_bgr.astype(np.float32)

    # 5. Frequency Separation (Tone smoothing strictly inside skin mask with pore preservation)
    skin_smoothing = float(preset_dict.get("skin_smoothing", 0.50))
    skin_mask_f = (cv2.GaussianBlur(skin_mask, (15, 15), 0).astype(np.float32) / 255.0)[:, :, None]

    low_freq = cv2.GaussianBlur(healed_f, (15, 15), 0)
    high_freq = healed_f - low_freq + 128.0

    low_u8 = np.clip(low_freq, 0, 255).astype(np.uint8)
    smoothed_low = cv2.bilateralFilter(low_u8, d=11, sigmaColor=24, sigmaSpace=11).astype(np.float32)

    # T-Zone Specular De-Shine
    shine_cut = float(preset_dict.get("shine_reduction", 0.30))
    if shine_cut > 0.05:
        gray_low = cv2.cvtColor(low_u8, cv2.COLOR_BGR2GRAY)
        _, shine_pts = cv2.threshold(gray_low, 185, 255, cv2.THRESH_BINARY)
        shine_pts = cv2.bitwise_and(shine_pts, skin_mask)
        shine_blur = (cv2.GaussianBlur(shine_pts, (15, 15), 0).astype(np.float32) / 255.0)[:, :, None]
        smoothed_low = smoothed_low * (1.0 - shine_blur * shine_cut * 0.25)

    blended_low = low_freq * (1.0 - skin_smoothing) + smoothed_low * skin_smoothing
    skin_recombined = np.clip(blended_low + high_freq - 128.0, 0, 255)
    base = skin_recombined * skin_mask_f + healed_f * (1.0 - skin_mask_f)

    # 6. Natural Lip Enhancement
    lip_enhancement = float(preset_dict.get("lip_enhancement", 0.30))
    lip_color = preset_dict.get("lip_color")
    lip_intensity = float(preset_dict.get("lip_intensity", 0.0))
    base = enhance_lips_natural(base, lips_mask, lip_enhancement=lip_enhancement, lip_color_hex=lip_color, lip_intensity=lip_intensity)

    # 7. Refined Eye Clarity & Catchlights (strictly inside eye mask, no white rings)
    eye_sharpen = float(preset_dict.get("eye_sharpen", 0.20))
    catchlight_boost = float(preset_dict.get("eye_catchlight", preset_dict.get("catchlight_boost", 0.20)))
    base = enhance_eyes_refined(base, eyes_mask, eye_sharpen=eye_sharpen, catchlight_boost=catchlight_boost)

    # 8. Soft Highlight Bloom (Glow on skin highlights only)
    glow_intensity = float(preset_dict.get("glow_intensity", 0.20))
    base = apply_subsurface_melanin_radiance(base, skin_mask_f, glow_intensity=glow_intensity)

    # 9. Cap & Gown Clarity + Highlight Recovery
    highlight_recovery = float(preset_dict.get("highlight_recovery", 0.60))
    base = enhance_clothing_and_regalia(base, hat_mask, cloth_mask, clarity_strength=0.35, highlight_recovery=highlight_recovery)

    # 10. Studio Environment Lighting (Soft key light + S-curve)
    lighting_temp = preset_dict.get("lighting_temp", "neutral_5500k")
    studio_light = float(preset_dict.get("studio_light_intensity", 0.18))
    rim_boost = float(preset_dict.get("rim_light_boost", 0.15))
    effective_subject_mask = subject_mask
    if effective_subject_mask is None:
        effective_subject_mask = cv2.bitwise_or(skin_mask, cloth_mask)
        if "hair" in masks:
            effective_subject_mask = cv2.bitwise_or(effective_subject_mask, masks["hair"])
        if "hat" in masks:
            effective_subject_mask = cv2.bitwise_or(effective_subject_mask, hat_mask)

    base = apply_studio_environment_lighting(
        base,
        subject_mask=effective_subject_mask,
        lighting_temp=lighting_temp,
        studio_light_intensity=studio_light,
        rim_light_boost=rim_boost,
        face_info=face_info
    )

    # 11. Realism Fidelity Blending
    fidelity_weight = float(preset_dict.get("fidelity_weight", 0.80))
    final = base * (1.0 - fidelity_weight * 0.15) + img_f * (fidelity_weight * 0.15)

    # 12. Aftershoot-Style AI Color Profiles & Tonal Grading
    color_profile_id = preset_dict.get("color_profile", "clean_commercial")
    color_warmth = float(preset_dict.get("color_warmth", 0.0))
    color_contrast = float(preset_dict.get("color_contrast", 0.0))
    color_vibrance = float(preset_dict.get("color_vibrance", 0.0))

    final = apply_aftershoot_color_grading(
        final,
        profile_id=color_profile_id,
        warmth=color_warmth,
        contrast=color_contrast,
        vibrance=color_vibrance,
        skin_mask_f=skin_mask_f
    )

    return np.clip(final, 0, 255).astype(np.uint8)


# =========================================================================
# AFTERSHOOT-STYLE COLOR PROFILES & PROFESSIONAL LUT GRADING ENGINE
# =========================================================================

AFTERSHOOT_COLOR_PROFILES: Dict[str, Dict[str, Any]] = {
    "clean_commercial": {
        "id": "clean_commercial",
        "name": "Clean Commercial Studio",
        "category": "Commercial",
        "badge": "True-to-Life",
        "description": "Clean neutral daylight balance, clean whites, balanced skin tones, and modern commercial clarity.",
        "base_warmth": 0.0,
        "base_contrast": 0.08,
        "base_vibrance": 0.10,
        "shadow_lift": 0.05,
        "highlight_pull": 0.05,
        "is_monochrome": False
    },
    "warm_editorial": {
        "id": "warm_editorial",
        "name": "Warm Editorial Magazine",
        "category": "Editorial",
        "badge": "Vogue Style",
        "description": "Lush honeyed highlights, rich mocha shadow tone, and sun-kissed skin luminescence inspired by editorial pictorials.",
        "base_warmth": 0.18,
        "base_contrast": 0.12,
        "base_vibrance": 0.08,
        "shadow_lift": 0.08,
        "highlight_pull": 0.10,
        "is_monochrome": False
    },
    "cool_executive": {
        "id": "cool_executive",
        "name": "Cool Executive & Academic",
        "category": "Academic",
        "badge": "Corporate Crisp",
        "description": "Modern cool 6500K strobe contrast with sharp definition on black/navy suits and white collar seams.",
        "base_warmth": -0.15,
        "base_contrast": 0.14,
        "base_vibrance": 0.05,
        "shadow_lift": 0.02,
        "highlight_pull": 0.08,
        "is_monochrome": False
    },
    "golden_hour": {
        "id": "golden_hour",
        "name": "Golden Hour Radiance",
        "category": "Artistic",
        "badge": "Warm Sunset",
        "description": "Subtle amber warmth in midtones, lifted shadows, and gentle peach glow on facial skin.",
        "base_warmth": 0.25,
        "base_contrast": 0.06,
        "base_vibrance": 0.15,
        "shadow_lift": 0.10,
        "highlight_pull": 0.12,
        "is_monochrome": False
    },
    "vibrant_archival": {
        "id": "vibrant_archival",
        "name": "Vibrant Archival Print",
        "category": "Print Standard",
        "badge": "300 DPI Lab",
        "description": "Enhanced color depth optimized for archival photo lab printing. Rich regalia velvet, deep blacks, and protected skin.",
        "base_warmth": 0.02,
        "base_contrast": 0.15,
        "base_vibrance": 0.22,
        "shadow_lift": -0.02,
        "highlight_pull": 0.05,
        "is_monochrome": False
    },
    "cinematic_mood": {
        "id": "cinematic_mood",
        "name": "Cinematic Film Split-Tone",
        "category": "Cinematic",
        "badge": "3D LUT Style",
        "description": "Subtle split-toning with warm amber highlights and cool teal shadow depth for dramatic portrait framing.",
        "base_warmth": 0.08,
        "base_contrast": 0.18,
        "base_vibrance": 0.06,
        "shadow_lift": 0.12,
        "highlight_pull": 0.15,
        "is_monochrome": False
    },
    "monochrome_fine_art": {
        "id": "monochrome_fine_art",
        "name": "Monochrome Fine Art",
        "category": "Monochrome",
        "badge": "B&W Classic",
        "description": "Timeless graduation black-and-white tonal scale with deep blacks, luminous skin highlights, and rich grey gradation.",
        "base_warmth": 0.0,
        "base_contrast": 0.22,
        "base_vibrance": -1.0,
        "shadow_lift": 0.04,
        "highlight_pull": 0.06,
        "is_monochrome": True
    },
    "natural_raw": {
        "id": "natural_raw",
        "name": "Natural Camera Authentic",
        "category": "Neutral",
        "badge": "Zero Shift",
        "description": "Unaltered camera sensor color balance with pure dynamic range protection.",
        "base_warmth": 0.0,
        "base_contrast": 0.0,
        "base_vibrance": 0.0,
        "shadow_lift": 0.0,
        "highlight_pull": 0.0,
        "is_monochrome": False
    }
}


def apply_aftershoot_color_grading(
    img_f: np.ndarray,
    profile_id: str = "clean_commercial",
    warmth: float = 0.0,
    contrast: float = 0.0,
    vibrance: float = 0.0,
    skin_mask_f: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Executes professional color grading inspired by Aftershoot Edits & 3D LUT profiles:
      1. Tonal curve adjustments (parametric S-curve, shadow lift, highlight compression).
      2. Color temperature (Kelvin shift) and split-toning.
      3. Skin-tone protected smart vibrance (protects human skin melanin from oversaturation).
      4. Support for high-contrast Monochrome Fine Art B&W grading.
    """
    profile = AFTERSHOOT_COLOR_PROFILES.get(profile_id, AFTERSHOOT_COLOR_PROFILES["clean_commercial"])
    out = img_f.copy()

    # 1. Monochrome Mode check
    if profile.get("is_monochrome", False):
        gray = 0.114 * out[:, :, 0] + 0.587 * out[:, :, 1] + 0.299 * out[:, :, 2]
        norm_g = np.clip(gray / 255.0, 0.0, 1.0)
        eff_contrast = profile.get("base_contrast", 0.20) + (contrast / 100.0)
        s_curve = norm_g * norm_g * (3.0 - 2.0 * norm_g)
        graded_g = (norm_g * (1.0 - eff_contrast) + s_curve * eff_contrast) * 255.0
        # Replicate across 3 BGR channels
        out[:, :, 0] = graded_g
        out[:, :, 1] = graded_g
        out[:, :, 2] = graded_g
        return np.clip(out, 0, 255)

    # 2. Parametric Tone Curve (Contrast, Shadow Lift, Highlight Compression)
    eff_contrast = profile.get("base_contrast", 0.0) + (contrast / 100.0)
    shadow_lift = profile.get("shadow_lift", 0.0)
    highlight_pull = profile.get("highlight_pull", 0.0)

    norm = np.clip(out / 255.0, 0.0, 1.0)
    if abs(eff_contrast) > 0.01:
        s_curve = norm * norm * (3.0 - 2.0 * norm)
        if eff_contrast > 0:
            norm = norm * (1.0 - eff_contrast) + s_curve * eff_contrast
        else:
            # Flatten contrast
            norm = norm * (1.0 + eff_contrast) + 0.5 * (-eff_contrast)

    if shadow_lift > 0.01:
        # Lift deep shadows gracefully (< 0.5)
        shadow_mask = np.maximum(0.0, 0.5 - norm)
        norm += shadow_mask * shadow_lift * 0.45

    if highlight_pull > 0.01:
        # Tame blown-out highlights (> 0.6)
        highlight_mask = np.maximum(0.0, norm - 0.6)
        norm -= highlight_mask * highlight_pull * 0.35

    out = norm * 255.0

    # 3. White Balance & Temperature (Kelvin shift)
    eff_warmth = profile.get("base_warmth", 0.0) + (warmth / 100.0)
    if abs(eff_warmth) > 0.01:
        # In BGR: Channel 0 = Blue, Channel 1 = Green, Channel 2 = Red
        # Warmth lifts Red & slightly Green, reduces Blue
        w_factor = eff_warmth * 18.0
        out[:, :, 2] = np.clip(out[:, :, 2] + w_factor * 1.0, 0, 255)
        out[:, :, 1] = np.clip(out[:, :, 1] + w_factor * 0.3, 0, 255)
        out[:, :, 0] = np.clip(out[:, :, 0] - w_factor * 0.9, 0, 255)

    # 4. Split-Toning for Cinematic Profile
    if profile_id == "cinematic_mood":
        lum = (0.114 * out[:, :, 0] + 0.587 * out[:, :, 1] + 0.299 * out[:, :, 2]) / 255.0
        hi_weight = np.clip((lum - 0.5) * 2.0, 0.0, 1.0)[:, :, None]
        lo_weight = np.clip((0.5 - lum) * 2.0, 0.0, 1.0)[:, :, None]

        # Warm amber in highlights: +Red, +Green
        out[:, :, 2] += hi_weight[:, :, 0] * 12.0
        out[:, :, 1] += hi_weight[:, :, 0] * 6.0
        # Cool teal in shadows: +Blue, +Green
        out[:, :, 0] += lo_weight[:, :, 0] * 14.0
        out[:, :, 1] += lo_weight[:, :, 0] * 5.0

    # 5. Smart Vibrance (Skin Tone Melanin Protection)
    eff_vibrance = profile.get("base_vibrance", 0.0) + (vibrance / 100.0)
    if abs(eff_vibrance) > 0.01:
        u8 = np.clip(out, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(u8, cv2.COLOR_BGR2HSV).astype(np.float32)
        h, s, v = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]

        # In OpenCV, Hue is 0-180. Human skin tone is typically H in [5, 25]
        is_skin_hue = (h >= 5) & (h <= 25)
        skin_protect_factor = np.where(is_skin_hue, 0.35, 1.0)
        if skin_mask_f is not None:
            # Extra protection inside detected skin mask
            sm = skin_mask_f[:, :, 0] if len(skin_mask_f.shape) == 3 else skin_mask_f
            skin_protect_factor = skin_protect_factor * (1.0 - sm * 0.5)

        # Vibrance boosts low saturation pixels more than already saturated ones
        sat_norm = s / 255.0
        vib_boost = (1.0 - sat_norm) * eff_vibrance * 70.0 * skin_protect_factor
        hsv[:, :, 1] = np.clip(s + vib_boost, 0.0, 255.0)

        out = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    return np.clip(out, 0, 255)

