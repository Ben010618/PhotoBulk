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
        "fidelity_weight": 0.85,
        "teeth_whitening": 0.30,
        "skin_brightening": 0.0
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
        "fidelity_weight": 0.75,
        "teeth_whitening": 0.45,
        "skin_brightening": 0.25
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
        "fidelity_weight": 0.80,
        "teeth_whitening": 0.50,
        "skin_brightening": 0.15
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


def _face_width(face_info: Optional[Dict[str, Any]], shape: Tuple[int, ...]) -> float:
    """Face width in pixels; all retouch kernels scale with it so preview and full-res match."""
    if face_info and "bbox" in face_info:
        return float(max(int(face_info["bbox"][2]), 16))
    return float(max(shape[:2]) * 0.25)


def _odd(n: float, minimum: int = 3) -> int:
    return max(minimum, int(round(n)) | 1)


def _mask_roi(mask: np.ndarray, pad: int) -> Optional[Tuple[int, int, int, int]]:
    ys, xs = np.where(mask > 0)
    if len(ys) == 0:
        return None
    h, w = mask.shape[:2]
    return (max(0, int(ys.min()) - pad), min(h, int(ys.max()) + pad + 1),
            max(0, int(xs.min()) - pad), min(w, int(xs.max()) + pad + 1))


def _soft_mask(mask: np.ndarray, blur_px: float) -> np.ndarray:
    k = _odd(blur_px)
    return (cv2.GaussianBlur(mask, (k, k), 0).astype(np.float32) / 255.0)[:, :, None]


def _nostril_exclusion(shape: Tuple[int, ...], face_info: Optional[Dict[str, Any]]) -> np.ndarray:
    """Mask over the nostrils, which are dark blobs a spot detector would otherwise heal."""
    excl = np.zeros(shape[:2], dtype=np.uint8)
    if face_info and face_info.get("nose") and "bbox" in face_info:
        fw, fh = face_info["bbox"][2], face_info["bbox"][3]
        nx, ny = face_info["nose"][:2]
        cv2.ellipse(excl, (int(nx), int(ny + fh * 0.05)), (max(2, int(fw * 0.17)), max(2, int(fh * 0.08))), 0, 0, 360, 255, -1)
    return excl


def detect_and_heal_blemishes(
    img_bgr: np.ndarray,
    skin_mask: np.ndarray,
    blemish_strength: float = 0.60,
    keep_moles: bool = True,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Detects acne, dark spots and red pimples inside the skin mask and inpaints them.
    Dark spots come from a Black-Hat transform on L*, red acne from a* raised above
    its local median. Kernel sizes scale with face width. With keep_moles, very dark
    compact round marks (beauty marks) are left alone.
    """
    if blemish_strength <= 0.02 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_bgr

    fw = _face_width(face_info, img_bgr.shape)
    roi = _mask_roi(skin_mask, int(fw * 0.06) + 2)
    if roi is None:
        return img_bgr
    y1, y2, x1, x2 = roi
    roi_img = img_bgr[y1:y2, x1:x2]

    # Detect only well inside the skin (avoids hairline / jaw shadows) and away from nostrils
    erode_k = _odd(fw * 0.02)
    detect_mask = cv2.erode(skin_mask, np.ones((erode_k, erode_k), np.uint8))
    detect_mask = cv2.bitwise_and(detect_mask, cv2.bitwise_not(_nostril_exclusion(img_bgr.shape, face_info)))
    roi_mask = detect_mask[y1:y2, x1:x2]

    lab = cv2.cvtColor(roi_img, cv2.COLOR_BGR2LAB)
    L, A = lab[:, :, 0], lab[:, :, 1]

    k = _odd(fw * 0.08)  # spots up to ~8% of face width
    blackhat = cv2.morphologyEx(L, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    a_med = cv2.medianBlur(A, min(_odd(k * 2), 255))
    redness = cv2.subtract(A, a_med)

    # Typical acne / dark-spot contrast is 12-30 L* units; shading and creases are removed by the shape filter below
    dark_thr = 28.0 - 16.0 * blemish_strength
    red_thr = 16.0 - 8.0 * blemish_strength
    max_area = np.pi * (fw * 0.045) ** 2
    mole_min_area = np.pi * (fw * 0.008) ** 2
    heal_mask = np.zeros(roi_mask.shape, dtype=np.uint8)

    def collect(response: np.ndarray, candidates: np.ndarray, depth: int, check_moles: bool) -> None:
        """Keeps compact spot-sized components; a rejected component (a spot merged with a
        smile line or nose shading) is re-thresholded at higher contrast to split the spot out."""
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(candidates, connectivity=8)
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < 2:
                continue
            bw, bh = stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]
            comp = labels == i
            compact = max(bw, bh) <= 3.0 * max(min(bw, bh), 1) and area >= 0.3 * bw * bh
            if area <= max_area and compact:
                if check_moles and keep_moles and area >= mole_min_area:
                    roundish = 0.7 <= bw / max(bh, 1) <= 1.4
                    if roundish and float(np.mean(response[comp])) > 50.0:
                        continue
                heal_mask[comp] = 255
            elif depth < 3:
                vals = response[comp]
                sub_thr = float(vals.mean() + 0.5 * vals.std())
                sub = (comp & (response > sub_thr)).astype(np.uint8) * 255
                if cv2.countNonZero(sub) > 0:
                    collect(response, sub, depth + 1, check_moles)

    opening = np.ones((2, 2), np.uint8)
    dark = cv2.morphologyEx(cv2.bitwise_and(((blackhat > dark_thr).astype(np.uint8) * 255), roi_mask), cv2.MORPH_OPEN, opening)
    collect(blackhat, dark, 0, check_moles=True)
    red = cv2.morphologyEx(cv2.bitwise_and(((redness > red_thr).astype(np.uint8) * 255), roi_mask), cv2.MORPH_OPEN, opening)
    collect(redness, red, 0, check_moles=False)

    if cv2.countNonZero(heal_mask) == 0:
        return img_bgr

    dil_k = _odd(fw * 0.012)
    heal_mask = cv2.dilate(heal_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dil_k, dil_k)))
    inpainted = cv2.inpaint(roi_img, heal_mask, inpaintRadius=max(3, int(fw * 0.015)), flags=cv2.INPAINT_TELEA)
    alpha = float(np.clip(blemish_strength * 1.6, 0.0, 1.0))
    alpha_heal = _soft_mask(heal_mask, fw * 0.01) * alpha
    roi_healed = inpainted.astype(np.float32) * alpha_heal + roi_img.astype(np.float32) * (1.0 - alpha_heal)
    out = img_bgr.copy()
    out[y1:y2, x1:x2] = np.clip(roi_healed, 0, 255).astype(np.uint8)
    return out


def correct_spots_and_even_skin_tone(
    img_bgr: np.ndarray,
    skin_mask: np.ndarray,
    spot_correction: float = 0.50,
    eyes_mask: Optional[np.ndarray] = None,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Evens out dark patches, hyperpigmentation and blotchy redness by pulling each skin
    pixel toward the local median skin tone (like foundation), plus under-eye concealer.
    Only darker-than-surrounding and redder-than-surrounding deviations are corrected,
    so the student's overall skin tone is not bleached.
    """
    if spot_correction <= 0.02 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_bgr

    fw = _face_width(face_info, img_bgr.shape)
    roi = _mask_roi(skin_mask, int(fw * 0.10) + 2)
    if roi is None:
        return img_bgr
    y1, y2, x1, x2 = roi
    roi_bgr = img_bgr[y1:y2, x1:x2]
    roi_lab = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)

    # Clean-skin reference: a morphological closing fills dark patches smaller than ~15% of the
    # face (spots, blotches) while following broad shading; an opening on a* removes red blotches.
    # Computed at a fixed working scale and smoothed so the correction has no hard contours.
    scale = min(1.0, 160.0 / fw)
    small = cv2.resize(roi_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else roi_bgr
    small_lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    kc = _odd(fw * scale * 0.15)
    se = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kc, kc))
    ref_small = np.dstack([
        cv2.morphologyEx(small_lab[:, :, 0], cv2.MORPH_CLOSE, se),
        cv2.morphologyEx(small_lab[:, :, 1], cv2.MORPH_OPEN, se),
        small_lab[:, :, 2],
    ]).astype(np.float32)
    ref_small = cv2.GaussianBlur(ref_small, (0, 0), kc / 3.0)
    ref_lab = cv2.resize(ref_small, (roi_bgr.shape[1], roi_bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
    # Compare against a lightly blurred image so individual pores are not lifted away
    cur_lab = cv2.GaussianBlur(roi_lab, (0, 0), max(0.8, fw * 0.006))

    skin_f = _soft_mask(skin_mask[y1:y2, x1:x2], fw * 0.03)[:, :, 0]
    s = float(np.clip(spot_correction, 0.0, 1.0))

    dark_deficit = np.maximum(0.0, ref_lab[:, :, 0] - cur_lab[:, :, 0])
    roi_lab[:, :, 0] += dark_deficit * (s * 0.85) * skin_f
    red_excess = np.maximum(0.0, cur_lab[:, :, 1] - ref_lab[:, :, 1])
    roi_lab[:, :, 1] -= red_excess * (s * 0.80) * skin_f
    b_dev = cur_lab[:, :, 2] - ref_lab[:, :, 2]
    roi_lab[:, :, 2] -= b_dev * (s * 0.40) * skin_f
    median_lab = ref_lab

    if eyes_mask is not None and cv2.countNonZero(eyes_mask[y1:y2, x1:x2]) > 0:
        roi_eyes = eyes_mask[y1:y2, x1:x2]
        e_ys, e_xs = np.where(roi_eyes > 0)
        eye_h = max(2, int(e_ys.max() - e_ys.min()))
        ue_y1 = int(e_ys.max())
        ue_y2 = min(roi_bgr.shape[0], ue_y1 + int(eye_h * 0.9))
        ue_mask = np.zeros(roi_lab.shape[:2], dtype=np.float32)
        ue_mask[ue_y1:ue_y2, max(0, int(e_xs.min())):int(e_xs.max())] = 1.0
        k_ue = _odd(fw * 0.05)
        ue_mask = cv2.GaussianBlur(ue_mask, (k_ue, k_ue), 0) * skin_f
        ue_dark = np.maximum(0.0, median_lab[:, :, 0] + 4.0 - roi_lab[:, :, 0])
        roi_lab[:, :, 0] += ue_dark * (s * 0.5) * ue_mask

    out = img_bgr.copy()
    out[y1:y2, x1:x2] = cv2.cvtColor(np.clip(roi_lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
    return out


def smooth_skin_frequency_separation(
    img_f: np.ndarray,
    skin_mask: np.ndarray,
    strength: float,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Pore-preserving skin smoothing. An edge-preserving blur is computed at a fixed working
    scale (face ~256 px wide) so it removes uneven texture and blotches the same way on a
    preview and a 24 MP master; fine pore grain from the original is re-injected.
    """
    if strength <= 0.02 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_f

    fw = _face_width(face_info, img_f.shape)
    roi = _mask_roi(skin_mask, int(fw * 0.05) + 2)
    if roi is None:
        return img_f
    y1, y2, x1, x2 = roi
    roi_f = img_f[y1:y2, x1:x2]
    rh, rw = roi_f.shape[:2]

    scale = min(1.0, 256.0 / fw)
    roi_u8 = np.clip(roi_f, 0, 255).astype(np.uint8)
    small = cv2.resize(roi_u8, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else roi_u8
    sm = cv2.bilateralFilter(small, d=9, sigmaColor=26, sigmaSpace=7)
    sm = cv2.bilateralFilter(sm, d=9, sigmaColor=18, sigmaSpace=7)
    delta = sm.astype(np.float32) - small.astype(np.float32)
    if scale < 1.0:
        delta = cv2.resize(delta, (rw, rh), interpolation=cv2.INTER_LINEAR)
    smoothed = roi_f + delta

    # Re-inject a portion of the finest grain so skin keeps real pores instead of looking plastic
    grain_sigma = max(0.8, fw / 256.0)
    grain = roi_f - cv2.GaussianBlur(roi_f, (0, 0), grain_sigma)
    smoothed = smoothed + grain * (0.45 if scale < 1.0 else 0.35)

    # Full slider = 85% blend so even maximum smoothing keeps some real skin structure
    m = _soft_mask(skin_mask[y1:y2, x1:x2], fw * 0.03) * float(np.clip(strength, 0.0, 1.0)) * 0.85
    out = img_f.copy()
    out[y1:y2, x1:x2] = roi_f * (1.0 - m) + smoothed * m
    return out


def reduce_skin_shine(
    img_f: np.ndarray,
    skin_mask: np.ndarray,
    strength: float,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """Tames oily T-zone hot spots: pulls skin brighter than the typical skin tone back down and restores its colour."""
    if strength <= 0.02 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_f

    fw = _face_width(face_info, img_f.shape)
    roi = _mask_roi(skin_mask, 2)
    if roi is None:
        return img_f
    y1, y2, x1, x2 = roi
    roi_u8 = np.clip(img_f[y1:y2, x1:x2], 0, 255).astype(np.uint8)
    lab = cv2.cvtColor(roi_u8, cv2.COLOR_BGR2LAB).astype(np.float32)
    in_skin = skin_mask[y1:y2, x1:x2] > 127
    if np.count_nonzero(in_skin) < 50:
        return img_f

    L = lab[:, :, 0]
    ref_L = float(np.percentile(L[in_skin], 60))
    excess = np.maximum(0.0, L - (ref_L + 10.0))
    excess = cv2.GaussianBlur(excess, (0, 0), max(1.0, fw * 0.012))
    s = float(np.clip(strength, 0.0, 1.0))
    lab[:, :, 0] = L - excess * s * 0.80

    # Shine is desaturated; blend chroma back toward the typical skin colour
    w_col = np.clip(excess / 30.0, 0.0, 1.0) * s * 0.7
    for c in (1, 2):
        ref_c = float(np.median(lab[:, :, c][in_skin]))
        lab[:, :, c] = lab[:, :, c] + (ref_c - lab[:, :, c]) * w_col

    fixed = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    m = _soft_mask(skin_mask[y1:y2, x1:x2], fw * 0.02)
    out = img_f.copy()
    out[y1:y2, x1:x2] = img_f[y1:y2, x1:x2] * (1.0 - m) + fixed * m
    return out


def brighten_skin(
    img_f: np.ndarray,
    skin_mask: np.ndarray,
    strength: float,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Skin brightening (fairer, luminous look) on face, neck and ears. Lifts luminance with a
    curve that raises darker skin more than highlights, and slightly reduces yellowness.
    Hue is kept, so the result is brighter skin rather than grey or chalky skin.
    """
    if strength <= 0.02 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_f

    fw = _face_width(face_info, img_f.shape)
    roi = _mask_roi(skin_mask, int(fw * 0.04) + 2)
    if roi is None:
        return img_f
    y1, y2, x1, x2 = roi
    roi_u8 = np.clip(img_f[y1:y2, x1:x2], 0, 255).astype(np.uint8)
    lab = cv2.cvtColor(roi_u8, cv2.COLOR_BGR2LAB).astype(np.float32)
    s = float(np.clip(strength, 0.0, 1.0))
    L = lab[:, :, 0]
    lab[:, :, 0] = L + s * 34.0 * np.power(np.clip(1.0 - L / 255.0, 0.0, 1.0), 0.8)
    lab[:, :, 2] = lab[:, :, 2] - (lab[:, :, 2] - 128.0) * s * 0.18
    bright = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)

    m = _soft_mask(skin_mask[y1:y2, x1:x2], fw * 0.05)
    out = img_f.copy()
    out[y1:y2, x1:x2] = img_f[y1:y2, x1:x2] * (1.0 - m) + bright * m
    return out


def _teeth_weight(
    img_f: np.ndarray,
    lips_mask: Optional[np.ndarray],
    face_info: Optional[Dict[str, Any]] = None,
    mouth_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """Soft 0..1 map of visible teeth: bright, low-redness pixels inside the mouth region."""
    h, w = img_f.shape[:2]
    weight = np.zeros((h, w), dtype=np.float32)
    region = mouth_mask if mouth_mask is not None and cv2.countNonZero(mouth_mask) > 0 else lips_mask
    if (region is None or cv2.countNonZero(region) == 0) and face_info and face_info.get("right_mouth") and face_info.get("left_mouth"):
        region = np.zeros((h, w), dtype=np.uint8)
        (rx, ry), (lx, ly) = face_info["right_mouth"][:2], face_info["left_mouth"][:2]
        fh = face_info["bbox"][3]
        cv2.ellipse(region, (int((rx + lx) / 2), int((ry + ly) / 2 + fh * 0.02)), (max(2, int(abs(lx - rx) * 0.5)), max(2, int(fh * 0.07))), 0, 0, 360, 255, -1)
    if region is None or cv2.countNonZero(region) == 0:
        return weight

    y1, y2, x1, x2 = _mask_roi(region, 2)
    lab = cv2.cvtColor(np.clip(img_f[y1:y2, x1:x2], 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    in_reg = region[y1:y2, x1:x2] > 127
    if np.count_nonzero(in_reg) < 10:
        return weight
    L, A = lab[:, :, 0], lab[:, :, 1]
    l_thr = max(110.0, float(np.percentile(L[in_reg], 45)))
    w_map = np.clip((150.0 - A) / 10.0, 0.0, 1.0) * np.clip((L - l_thr) / 18.0, 0.0, 1.0) * in_reg
    weight[y1:y2, x1:x2] = cv2.GaussianBlur(w_map.astype(np.float32), (3, 3), 0)
    return weight


def whiten_teeth(img_f: np.ndarray, teeth_weight: Optional[np.ndarray], strength: float) -> np.ndarray:
    """Natural teeth whitening: removes yellow (b*) and lifts brightness only on detected teeth."""
    if strength <= 0.02 or teeth_weight is None or not np.any(teeth_weight > 0.05):
        return img_f
    y1, y2, x1, x2 = _mask_roi((teeth_weight > 0.02).astype(np.uint8), 2)
    lab = cv2.cvtColor(np.clip(img_f[y1:y2, x1:x2], 0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32)
    s = float(np.clip(strength, 0.0, 1.0))
    lab[:, :, 2] -= np.maximum(0.0, lab[:, :, 2] - 128.0) * s * 0.85
    lab[:, :, 1] -= np.maximum(0.0, lab[:, :, 1] - 128.0) * s * 0.30
    lab[:, :, 0] += s * 32.0 * np.clip(1.0 - lab[:, :, 0] / 255.0, 0.0, 1.0)
    white = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR).astype(np.float32)
    m = teeth_weight[y1:y2, x1:x2][:, :, None]
    out = img_f.copy()
    out[y1:y2, x1:x2] = img_f[y1:y2, x1:x2] * (1.0 - m) + white * m
    return out


def iron_fabric_wrinkles(
    img_f: np.ndarray,
    cloth_mask: Optional[np.ndarray],
    strength: float,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """Digital toga ironing: flattens low-contrast wrinkle shading on the gown while keeping seams and fold edges."""
    if strength <= 0.02 or cloth_mask is None or cv2.countNonZero(cloth_mask) == 0:
        return img_f
    fw = _face_width(face_info, img_f.shape)
    y1, y2, x1, x2 = _mask_roi(cloth_mask, 2)
    roi_f = img_f[y1:y2, x1:x2]
    rh, rw = roi_f.shape[:2]
    scale = min(1.0, 220.0 / fw)
    roi_u8 = np.clip(roi_f, 0, 255).astype(np.uint8)
    small = cv2.resize(roi_u8, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1.0 else roi_u8
    sm = cv2.bilateralFilter(small, d=9, sigmaColor=16, sigmaSpace=9)
    sm = cv2.bilateralFilter(sm, d=9, sigmaColor=14, sigmaSpace=9)
    delta = sm.astype(np.float32) - small.astype(np.float32)
    if scale < 1.0:
        delta = cv2.resize(delta, (rw, rh), interpolation=cv2.INTER_LINEAR)
    inner = cv2.erode(cloth_mask[y1:y2, x1:x2], np.ones((3, 3), np.uint8), iterations=2)
    m = _soft_mask(inner, fw * 0.02) * float(np.clip(strength, 0.0, 1.0)) * 0.9
    out = img_f.copy()
    out[y1:y2, x1:x2] = roi_f + delta * m
    return out


def cleanup_facial_stray_hairs(
    img_bgr: np.ndarray,
    skin_mask: np.ndarray,
    strength: float = 0.50,
    face_info: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """
    Removes thin dark stray hair strands lying on the forehead, cheeks and neck.
    Candidates are thin dark ridges (Black-Hat) that are clearly elongated; round spots
    are left to the blemish tool. Kernel sizes scale with face width.
    """
    if strength <= 0.02 or skin_mask is None or cv2.countNonZero(skin_mask) == 0:
        return img_bgr

    fw = _face_width(face_info, img_bgr.shape)
    roi = _mask_roi(skin_mask, int(fw * 0.03) + 2)
    if roi is None:
        return img_bgr
    y1, y2, x1, x2 = roi
    roi_img = img_bgr[y1:y2, x1:x2]
    roi_mask = skin_mask[y1:y2, x1:x2]

    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    k = _odd(fw * 0.035)
    bh = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    thr = 22.0 - 12.0 * strength
    stray = ((bh > thr).astype(np.uint8) * 255)
    stray = cv2.bitwise_and(stray, roi_mask)

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(stray, connectivity=8)
    final = np.zeros_like(stray)
    min_len = fw * 0.05
    for i in range(1, num_labels):
        area = stats[i, cv2.CC_STAT_AREA]
        length = float(max(stats[i, cv2.CC_STAT_WIDTH], stats[i, cv2.CC_STAT_HEIGHT]))
        if area < 4 or length < min_len:
            continue
        thickness = area / max(length, 1.0)
        if length / max(thickness, 0.5) >= 5.0:
            final[labels == i] = 255

    if cv2.countNonZero(final) == 0:
        return img_bgr

    inpaint_mask = cv2.dilate(final, np.ones((3, 3), np.uint8), iterations=1 + int(fw > 400))
    inpainted = cv2.inpaint(roi_img, inpaint_mask, inpaintRadius=max(3, int(fw * 0.012)), flags=cv2.INPAINT_TELEA)
    alpha = _soft_mask(inpaint_mask, 3) * float(np.clip(strength * 1.6, 0.0, 1.0))
    roi_cleaned = inpainted.astype(np.float32) * alpha + roi_img.astype(np.float32) * (1.0 - alpha)
    out = img_bgr.copy()
    out[y1:y2, x1:x2] = np.clip(roi_cleaned, 0, 255).astype(np.uint8)
    return out


def cleanup_flyaway_hair_alpha(
    alpha_mask: np.ndarray,
    hair_mask: Optional[np.ndarray] = None,
    strength: float = 0.50,
    protect_mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Removes thin flyaway strands sticking out of the hair silhouette into the backdrop.
    Works only in a band around the parsed hair region, and never touches protect_mask
    (cap, tassel), so mortarboard corners and tassel threads are not eroded.
    Without a hair mask it falls back to the top half of the frame.
    """
    if strength <= 0.02 or alpha_mask is None:
        return alpha_mask

    h, w = alpha_mask.shape[:2]
    ref = max(h, w)
    ksize = _odd(ref * 0.006 + strength * ref * 0.012)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ksize, ksize))

    if hair_mask is not None and cv2.countNonZero(hair_mask) > 0:
        band = _odd(ref * 0.04)
        hair_zone = cv2.dilate(hair_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (band, band)))
    else:
        hair_zone = np.zeros_like(alpha_mask)
        hair_zone[:int(h * 0.55), :] = 255
    if protect_mask is not None and cv2.countNonZero(protect_mask) > 0:
        guard = _odd(ref * 0.01)
        hair_zone = cv2.bitwise_and(hair_zone, cv2.bitwise_not(cv2.dilate(protect_mask, np.ones((guard, guard), np.uint8))))

    smoothed_alpha = cv2.morphologyEx(alpha_mask, cv2.MORPH_OPEN, kernel)
    weight = (cv2.GaussianBlur(hair_zone, (15, 15), 0).astype(np.float32) / 255.0) * float(np.clip(strength * 1.4, 0.0, 1.0))
    res = alpha_mask.astype(np.float32) * (1.0 - weight) + smoothed_alpha.astype(np.float32) * weight
    return np.clip(res, 0, 255).astype(np.uint8)


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
    roi_hsv[:, :, 2] = np.where(sclera, np.clip(v * (1.02 + 0.08 * catchlight_boost), 0, 255), v)

    # Specular catchlight: gentle glint enhancement, strictly inside pupil/iris
    if catchlight_boost > 0.05:
        in_eye = roi_mask > 50
        glint_thr = max(150.0, float(np.percentile(v[in_eye], 92))) if np.any(in_eye) else 190.0
        glint = in_eye & (v > glint_thr)
        v2 = roi_hsv[:, :, 2]
        roi_hsv[:, :, 2] = np.where(glint, np.clip(v2 + catchlight_boost * 45.0, 0, 255), v2)

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

    # 3. Key-light colour temperature (warm tungsten / cool daylight strobe) on the subject
    temp_shift = {"warm_3200k": 1.0, "warm_4500k": 0.5, "cool_6500k": -1.0}.get(lighting_temp, 0.0)
    if temp_shift:
        if subject_mask is not None:
            sm = subject_mask if subject_mask.ndim == 2 else cv2.cvtColor(subject_mask, cv2.COLOR_BGR2GRAY)
            t_w = (sm.astype(np.float32) / 255.0)[:, :, None]
        else:
            t_w = 1.0
        out = out + np.array([-9.0, 2.5, 9.0], dtype=np.float32) * temp_shift * t_w

    # 4. Gentle S-Curve for contrast
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
        lit = apply_studio_environment_lighting(
            img_f,
            subject_mask=subject_mask,
            lighting_temp=preset_dict.get("lighting_temp", "neutral_5500k"),
            studio_light_intensity=float(preset_dict.get("studio_light_intensity", 0.15) or 0.0),
            rim_light_boost=float(preset_dict.get("rim_light_boost", 0.0) or 0.0)
        )
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
    empty = np.zeros((h, w), dtype=np.uint8)
    skin_mask = masks.get("skin", empty)
    facial_skin = masks.get("facial_skin", skin_mask)
    eyes_mask = masks.get("eyes", empty)
    lips_mask = masks.get("lips", empty)
    hat_mask = masks.get("hat", empty)
    cloth_mask = masks.get("cloth", empty)
    ears_mask = masks.get("ears")

    def amount(key: str, default: float) -> float:
        try:
            return float(np.clip(float(preset_dict.get(key, default) or 0.0), 0.0, 1.0))
        except (TypeError, ValueError):
            return default

    # 2. Loose / stray hairs lying on the face
    if preset_dict.get("cleanup_loose_hair", True):
        img_bgr = cleanup_facial_stray_hairs(img_bgr, skin_mask, strength=amount("loose_hair_cleanup", 0.40), face_info=face_info)

    # 3. Acne & blemish healing (optionally keeping beauty marks)
    img_bgr = detect_and_heal_blemishes(
        img_bgr, skin_mask,
        blemish_strength=amount("blemish_cut", 0.60),
        keep_moles=bool(preset_dict.get("keep_moles", True)),
        face_info=face_info
    )

    # 4. Dark spot correction & even skin tone
    spot = preset_dict.get("spot_correction", preset_dict.get("dark_spot_whitening", 0.40))
    img_bgr = correct_spots_and_even_skin_tone(
        img_bgr, skin_mask,
        spot_correction=float(np.clip(float(spot or 0.0), 0.0, 1.0)),
        eyes_mask=eyes_mask,
        face_info=face_info
    )
    base = img_bgr.astype(np.float32)

    # 5. Pore-preserving smoothing, 6. T-zone shine control
    base = smooth_skin_frequency_separation(base, skin_mask, amount("skin_smoothing", 0.50), face_info)
    base = reduce_skin_shine(base, facial_skin, amount("shine_reduction", 0.30), face_info)

    # 7. Skin brightening (face, neck and ears)
    bright_mask = skin_mask if ears_mask is None else cv2.bitwise_or(skin_mask, ears_mask)
    base = brighten_skin(base, bright_mask, amount("skin_brightening", 0.0), face_info)

    # 8. Teeth whitening, then lips (teeth excluded so lip saturation never yellows them)
    teeth_w = _teeth_weight(base, lips_mask, face_info, masks.get("mouth"))
    base = whiten_teeth(base, teeth_w, amount("teeth_whitening", 0.0))
    lips_only = (lips_mask.astype(np.float32) * (1.0 - np.clip(teeth_w * 1.5, 0.0, 1.0))).astype(np.uint8)
    base = enhance_lips_natural(
        base, lips_only,
        lip_enhancement=amount("lip_enhancement", 0.30),
        lip_color_hex=preset_dict.get("lip_color"),
        lip_intensity=amount("lip_intensity", 0.0)
    )

    # 9. Eye clarity & catchlights
    base = enhance_eyes_refined(
        base, eyes_mask,
        eye_sharpen=amount("eye_sharpen", 0.20),
        catchlight_boost=float(np.clip(float(preset_dict.get("eye_catchlight", preset_dict.get("catchlight_boost", 0.20)) or 0.0), 0.0, 1.0))
    )

    # 10. Soft highlight glow on skin
    skin_mask_f = _soft_mask(skin_mask, _face_width(face_info, img_bgr.shape) * 0.03)
    base = apply_subsurface_melanin_radiance(base, skin_mask_f, glow_intensity=amount("glow_intensity", 0.20))

    # 11. Toga ironing, then cap & gown clarity + highlight recovery
    base = iron_fabric_wrinkles(base, cloth_mask, amount("iron_strength", 0.0), face_info)
    base = enhance_clothing_and_regalia(base, hat_mask, cloth_mask, clarity_strength=0.35, highlight_recovery=amount("highlight_recovery", 0.60))

    # 12. Studio Environment Lighting (key light, rim light, colour temperature, S-curve)
    effective_subject_mask = subject_mask
    if effective_subject_mask is None:
        effective_subject_mask = cv2.bitwise_or(skin_mask, cloth_mask)
        if "hair" in masks:
            effective_subject_mask = cv2.bitwise_or(effective_subject_mask, masks["hair"])
        effective_subject_mask = cv2.bitwise_or(effective_subject_mask, hat_mask)

    final = apply_studio_environment_lighting(
        base,
        subject_mask=effective_subject_mask,
        lighting_temp=preset_dict.get("lighting_temp", "neutral_5500k"),
        studio_light_intensity=amount("studio_light_intensity", 0.18),
        rim_light_boost=amount("rim_light_boost", 0.15),
        face_info=face_info
    )

    # 13. Aftershoot-Style AI Color Profiles & Tonal Grading
    final = apply_aftershoot_color_grading(
        final,
        profile_id=preset_dict.get("color_profile", "clean_commercial"),
        warmth=float(preset_dict.get("color_warmth", 0.0) or 0.0),
        contrast=float(preset_dict.get("color_contrast", 0.0) or 0.0),
        vibrance=float(preset_dict.get("color_vibrance", 0.0) or 0.0),
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
        neutral_guard = np.clip(sat_norm / 0.15, 0.0, 1.0)
        vib_boost = (1.0 - sat_norm) * neutral_guard * eff_vibrance * 70.0 * skin_protect_factor
        hsv[:, :, 1] = np.clip(s + vib_boost, 0.0, 255.0)

        out = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    return np.clip(out, 0, 255)

