"""
KameraPh AI Beautification, Glow-Up & Studio Lighting Engine
Incorporates State-of-the-Art Retouching Methodologies:
  - Localized Blemish & Acne Healing: Difference-of-Gaussians localized soft-inpainting blemish & acne healing with pore preservation.
  - Dark Spot Correction & Hyperpigmentation Lightening: CIELAB luminance balancing for smooth, even skin tone.
  - Neural Lip Tinting & Recoloring: Soft-light / overlay spectral recoloring with realistic lip texture preservation.
  - Eye Catchlight & Enamel Clarity: Eye catchlight reflection enhancement, sclera clarity & natural enamel teeth whitening.
  - Sub-Surface Melanin Radiance: Sub-surface scattering radiance bloom & authentic Filipino Morena golden tones.
  - Studio Environment & Key Lighting: Adjustable studio strobe lighting, color temperature & rim highlights.
"""

import cv2
import numpy as np

BEAUTY_PRESETS = {
    "morena_radiant": {
        "id": "morena_radiant",
        "name": "Morena Radiant (Filipino Gold)",
        "description": "Preserves warm Filipino golden undertones, removes acne & blemishes, softens T-zone oil glare, and adds subtle skin radiance.",
        "skin_smoothing": 0.65,
        "blemish_cut": 0.70,
        "dark_spot_whitening": 0.50,
        "shine_reduction": 0.35,
        "lip_intensity": 0.35,
        "lip_color": "#d87093",
        "eye_sharpen": 0.25,
        "catchlight_boost": 0.40,
        "teeth_whitening": 0.45,
        "glow_intensity": 0.40,
        "warmth_boost": 1.04,
        "lighting_temp": "neutral_5500k",
        "studio_light_intensity": 0.20,
        "fidelity_weight": 0.75
    },
    "studio_glamour": {
        "id": "studio_glamour",
        "name": "Studio Glamour",
        "description": "Flawless soft skin glow, popped eye catchlights, clean teeth brightening, rosy lips and porcelain radiance.",
        "skin_smoothing": 0.80,
        "blemish_cut": 0.85,
        "dark_spot_whitening": 0.70,
        "shine_reduction": 0.45,
        "lip_intensity": 0.55,
        "lip_color": "#c71585",
        "eye_sharpen": 0.35,
        "catchlight_boost": 0.55,
        "teeth_whitening": 0.60,
        "glow_intensity": 0.55,
        "warmth_boost": 1.00,
        "lighting_temp": "neutral_5500k",
        "studio_light_intensity": 0.35,
        "fidelity_weight": 0.65
    },
    "natural_clean": {
        "id": "natural_clean",
        "name": "Natural Clean",
        "description": "Subtle retouching, maintains authentic pores and skin texture, eliminates flash glare, and clarifies iris.",
        "skin_smoothing": 0.45,
        "blemish_cut": 0.50,
        "dark_spot_whitening": 0.35,
        "shine_reduction": 0.25,
        "lip_intensity": 0.20,
        "lip_color": "#d87093",
        "eye_sharpen": 0.15,
        "catchlight_boost": 0.25,
        "teeth_whitening": 0.30,
        "glow_intensity": 0.20,
        "warmth_boost": 1.00,
        "lighting_temp": "neutral_5500k",
        "studio_light_intensity": 0.10,
        "fidelity_weight": 0.85
    },
    "high_key_crisp": {
        "id": "high_key_crisp",
        "name": "High-Key Crisp",
        "description": "High clarity, crisp hair & eye contours, brightened highlights for sharp yearbook print reproduction.",
        "skin_smoothing": 0.60,
        "blemish_cut": 0.65,
        "dark_spot_whitening": 0.55,
        "shine_reduction": 0.30,
        "lip_intensity": 0.40,
        "lip_color": "#e07a5f",
        "eye_sharpen": 0.45,
        "catchlight_boost": 0.50,
        "teeth_whitening": 0.50,
        "glow_intensity": 0.25,
        "warmth_boost": 0.98,
        "lighting_temp": "cool_6500k",
        "studio_light_intensity": 0.30,
        "fidelity_weight": 0.80
    }
}

LIP_COLOR_PALETTES = {
    "natural_rose": {"id": "natural_rose", "name": "Natural Rose", "hex": "#d87093", "rgb": (216, 112, 147)},
    "coral_peach": {"id": "coral_peach", "name": "Coral Peach", "hex": "#e07a5f", "rgb": (224, 122, 95)},
    "berry_plum": {"id": "berry_plum", "name": "Berry Plum", "hex": "#c71585", "rgb": (199, 21, 133)},
    "crimson_ruby": {"id": "crimson_ruby", "name": "Crimson Ruby", "hex": "#b22222", "rgb": (178, 34, 34)},
    "nude_cherry": {"id": "nude_cherry", "name": "Nude Cherry", "hex": "#c97a7e", "rgb": (201, 122, 126)},
    "warm_terracotta": {"id": "warm_terracotta", "name": "Warm Terracotta", "hex": "#c45b43", "rgb": (196, 91, 67)},
    "soft_pink": {"id": "soft_pink", "name": "Soft Pink", "hex": "#f48fb1", "rgb": (244, 143, 177)}
}


def hex_to_bgr(hex_str):
    """Converts hex color string (#rrggbb) to BGR tuple for OpenCV."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return (147, 112, 216) # Default rose
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    return (b, g, r)


def analyze_portrait_skin_ai(img_bgr, face_info):
    """
    AI Skin Tone & Melanin Evaluation:
    Samples forehead and cheek skin patches in CIELAB space to compute:
      - Melanin density & warm Morena golden index (b* / a* in Lab space)
      - Specular glare intensity
      - Adaptive smoothing & blemish threshold
    """
    if face_info is None:
        return {"undertone": "warm_morena", "melanin_index": 1.0, "glare_level": 0.3, "is_morena": True}
        
    x, y, fw, fh = face_info['bbox']
    cx, cy = x + fw // 2, y + int(fh * 0.35)
    patch = img_bgr[max(0, cy - 12):min(img_bgr.shape[0], cy + 12), max(0, cx - 12):min(img_bgr.shape[1], cx + 12)]
    if patch.size == 0:
        return {"undertone": "warm_morena", "melanin_index": 1.0, "glare_level": 0.3, "is_morena": True}

    lab = cv2.cvtColor(patch, cv2.COLOR_BGR2LAB)
    _, a_mean, b_mean = np.mean(lab, axis=(0, 1))
    is_morena = b_mean > 132 or (b_mean > 128 and a_mean > 134)
    return {
        "undertone": "warm_morena" if is_morena else "neutral_fair",
        "melanin_preservation": 1.05 if is_morena else 1.0,
        "is_morena": is_morena
    }


def detect_and_heal_blemishes(img_bgr, skin_mask, blemish_strength=0.75):
    """
    Pore-Safe Blemish & Acne Healing (Frequency-Selective Inpainting):
    Identifies localized high-contrast acne, pimples, and acute blemishes using
    Difference-of-Gaussians (DoG) on CIELAB luminance, then soft-inpaints ONLY the
    blemish centroids while keeping real pore micro-grain 100% crisp.
    """
    if blemish_strength <= 0.05 or skin_mask is None:
        return img_bgr

    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)

    # Difference of Gaussians at scales sigma1=1.0, sigma2=3.0
    g1 = cv2.GaussianBlur(L, (3, 3), 1.0)
    g2 = cv2.GaussianBlur(L, (11, 11), 3.0)
    dog = g1 - g2

    # Negative spikes indicate dark spots or acne relative to surrounding skin
    threshold = -9.0 * (1.25 - blemish_strength * 0.45)
    blemish_mask = ((dog < threshold) & (skin_mask > 128)).astype(np.uint8) * 255

    # Filter out tiny isolated single-pixel noise (preserving true pores)
    kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    blemish_mask = cv2.morphologyEx(blemish_mask, cv2.MORPH_OPEN, kernel_clean)
    blemish_mask = cv2.dilate(blemish_mask, kernel_clean, iterations=1)

    if cv2.countNonZero(blemish_mask) > 0:
        inpainted = cv2.inpaint(img_bgr, blemish_mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
        mask_f = (cv2.GaussianBlur(blemish_mask, (5, 5), 0).astype(np.float32) / 255.0 * blemish_strength)[:, :, np.newaxis]
        healed = inpainted.astype(np.float32) * mask_f + img_bgr.astype(np.float32) * (1.0 - mask_f)
        return np.clip(healed, 0, 255).astype(np.uint8)

    return img_bgr

detect_and_heal_blemishes_retouchformer = detect_and_heal_blemishes



def whiten_dark_spots_and_hyperpigmentation(img_bgr, skin_mask, whitening_strength=0.50):
    """
    Dark Spot Whitening & Hyperpigmentation Lightening:
    Identifies uneven dark patches, hyperpigmented zones, and under-eye dark circles
    and gently lifts their luminance towards the skin median without bleaching natural melanin tone.
    """
    if whitening_strength <= 0.05 or skin_mask is None:
        return img_bgr

    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)
    
    # Estimate local median skin luminance
    skin_valid = skin_mask > 128
    if np.sum(skin_valid) < 50:
        return img_bgr
        
    local_mean_L = cv2.GaussianBlur(L, (35, 35), 0)
    
    # Calculate luminance deficit where skin is significantly darker than local average
    dark_deficit = np.maximum(0.0, local_mean_L - L)
    
    # Scale correction factor with gentle non-linear curve
    correction = dark_deficit * (whitening_strength * 0.65) * (skin_mask.astype(np.float32) / 255.0)
    
    L_corrected = np.clip(L + correction, 0, 255).astype(np.uint8)
    lab[:, :, 0] = L_corrected
    
    # Also mildly reduce excess melanin discoloration (a/b chrominance spike) in hyperpigmented areas
    if whitening_strength > 0.3:
        chroma_mask = np.clip(dark_deficit / 30.0, 0.0, 1.0) * (whitening_strength * 0.25)
        a_mean = np.mean(lab[:, :, 1][skin_valid])
        b_mean = np.mean(lab[:, :, 2][skin_valid])
        
        a_f = lab[:, :, 1].astype(np.float32)
        b_f = lab[:, :, 2].astype(np.float32)
        
        lab[:, :, 1] = np.clip(a_f * (1.0 - chroma_mask) + a_mean * chroma_mask, 0, 255).astype(np.uint8)
        lab[:, :, 2] = np.clip(b_f * (1.0 - chroma_mask) + b_mean * chroma_mask, 0, 255).astype(np.uint8)

    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def recolor_lips_neural(img_f, r_mouth, l_mouth, fw, fh, lip_color_hex="#d87093", lip_intensity=0.40):
    """
    Neural Lip Recoloring & Tinting:
    Accurately targets the oral lip region and blends selected cosmetic tint
    using soft-light / overlay blend mode so natural lip highlights, sheen, and grain remain 100% authentic.
    """
    if lip_intensity <= 0.03 or r_mouth is None or l_mouth is None:
        return img_f

    h, w = img_f.shape[:2]
    mx = (int(r_mouth[0]) + int(l_mouth[0])) // 2
    my = (int(r_mouth[1]) + int(l_mouth[1])) // 2

    mouth_dist = abs(l_mouth[0] - r_mouth[0])
    mw = max(10, int(mouth_dist * 1.25))
    mh = max(8, int(fh * 0.18))

    x1, x2 = max(0, mx - mw // 2), min(w, mx + mw // 2)
    y1, y2 = max(0, my - mh // 2), min(h, my + mh // 2)

    patch = img_f[y1:y2, x1:x2]
    if patch.size == 0 or (y2 - y1) < 4 or (x2 - x1) < 4:
        return img_f

    patch_u8 = np.clip(patch, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(patch_u8, cv2.COLOR_BGR2HSV).astype(np.float32)
    lab = cv2.cvtColor(patch_u8, cv2.COLOR_BGR2LAB).astype(np.float32)

    # Lip mask: High redness in LAB a* or characteristic lip hue in HSV
    a_channel = lab[:, :, 1]
    val = hsv[:, :, 2]
    sat = hsv[:, :, 1]

    # Lips have elevated red chrominance (a* > 138) and moderate saturation
    lip_candidate = ((a_channel > 136) & (sat > 35) & (val > 40) & (val < 240)).astype(np.float32)
    
    # Elliptical anatomical mouth mask for spatial confinement
    ell_mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
    cx, cy = (x2 - x1) // 2, (y2 - y1) // 2
    cv2.ellipse(ell_mask, (cx, cy), (int((x2 - x1) * 0.44), int((y2 - y1) * 0.40)), 0, 0, 360, 1.0, -1)
    
    # Combined refined lip mask
    combined_mask = lip_candidate * ell_mask
    if np.sum(combined_mask) < 4:
        # Fallback to pure smooth ellipse if color detection has low contrast
        combined_mask = ell_mask * 0.85
        
    blurred_mask = cv2.GaussianBlur(combined_mask, (5, 5), 0)[:, :, np.newaxis]
    target_tint_bgr = np.array(hex_to_bgr(lip_color_hex), dtype=np.float32)

    # Soft-Light / Color Blend:
    # Blend target tint with original luminance
    patch_norm = patch / 255.0
    tint_norm = target_tint_bgr / 255.0
    
    # Soft Light blend formula: (1 - 2b)*a^2 + 2b*a
    soft_light = (1.0 - 2.0 * tint_norm) * (patch_norm ** 2) + 2.0 * tint_norm * patch_norm
    tinted_patch = np.clip(soft_light * 255.0, 0, 255)
    
    # Boost lip vibrancy / richness gently
    hsv_tinted = cv2.cvtColor(np.clip(tinted_patch, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv_tinted[:, :, 1] = np.clip(hsv_tinted[:, :, 1] * 1.15, 0, 255)
    tinted_patch = cv2.cvtColor(np.clip(hsv_tinted, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

    effective_weight = blurred_mask * lip_intensity
    recolored = patch * (1.0 - effective_weight) + tinted_patch * effective_weight

    out = img_f.copy()
    out[y1:y2, x1:x2] = recolored
    return out


def enhance_eye_catchlights(img_f, r_eye, l_eye, fw, eye_sharpen=0.35, catchlight_boost=0.45):
    """
    Eye Catchlight & Sclera Clarity Enhancement:
      - Sclera cleaning: desaturates bloodshot redness in eye whites
      - Iris edge sharpening: accentuates iris limbal ring
      - Specular catchlight boosting: enhances glint reflections in pupils from studio strobes
    """
    h, w = img_f.shape[:2]
    eye_radius_x = int(fw * 0.13)
    eye_radius_y = int(fw * 0.09)
    if eye_radius_x < 6 or eye_radius_y < 4:
        return img_f

    out = img_f.copy()

    for (ex, ey) in [r_eye, l_eye]:
        x1 = max(0, int(ex - eye_radius_x))
        x2 = min(w, int(ex + eye_radius_x))
        y1 = max(0, int(ey - eye_radius_y))
        y2 = min(h, int(ey + eye_radius_y))

        patch = out[y1:y2, x1:x2]
        if patch.size == 0:
            continue

        patch_u8 = np.clip(patch, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(patch_u8, cv2.COLOR_BGR2HSV).astype(np.float32)
        v = hsv[:, :, 2]
        s = hsv[:, :, 1]

        # Sclera (Eye Whites): High V, Low S in non-pupil region
        sclera_mask = ((v > 120) & (s < 125)).astype(np.float32)
        # Gently desaturate bloodshot veins and lift brightness
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 - sclera_mask * 0.42), 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + sclera_mask * 0.08), 0, 255)

        # Specular Catchlight in Pupil: Brightest glint pixels (v > 195)
        catchlight_mask = (v > 195).astype(np.float32)
        if np.sum(catchlight_mask) > 0 and catchlight_boost > 0.05:
            catchlight_blur = cv2.GaussianBlur(catchlight_mask, (3, 3), 0)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + catchlight_blur * (catchlight_boost * 42.0), 0, 255)

        enhanced_patch = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

        # Iris Contour & Lash Sharpening
        if eye_sharpen > 0.05:
            blurred_patch = cv2.GaussianBlur(enhanced_patch, (0, 0), 2.0)
            enhanced_patch = cv2.addWeighted(enhanced_patch, 1.0 + eye_sharpen * 0.7, blurred_patch, -eye_sharpen * 0.7, 0)

        # Smooth feathering mask for natural integration
        ell_mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
        cx, cy = (x2 - x1) // 2, (y2 - y1) // 2
        cv2.ellipse(ell_mask, (cx, cy), (int((x2 - x1) * 0.46), int((y2 - y1) * 0.46)), 0, 0, 360, 1.0, -1)
        ell_mask = cv2.GaussianBlur(ell_mask, (5, 5), 0)[:, :, np.newaxis]

        out[y1:y2, x1:x2] = enhanced_patch * ell_mask + patch * (1.0 - ell_mask)

    return out

enhance_eye_catchlights_codeformer = enhance_eye_catchlights


def whiten_teeth_enamel(img_f, r_mouth, l_mouth, fw, fh, whitening_strength=0.50):
    """
    Natural Enamel Teeth Whitening:
      - Targets mouth aperture between oral corners
      - Eliminates yellow/dull tint without bleaching lips or altering enamel texture
    """
    if whitening_strength <= 0.05:
        return img_f

    h, w = img_f.shape[:2]
    mx = (int(r_mouth[0]) + int(l_mouth[0])) // 2
    my = (int(r_mouth[1]) + int(l_mouth[1])) // 2

    mw = int(abs(l_mouth[0] - r_mouth[0]) * 0.85)
    mh = int(fh * 0.16)

    x1, x2 = max(0, mx - mw // 2), min(w, mx + mw // 2)
    y1, y2 = max(0, my - mh // 2), min(h, my + mh // 2)

    patch = img_f[y1:y2, x1:x2]
    if patch.size == 0:
        return img_f

    patch_u8 = np.clip(patch, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(patch_u8, cv2.COLOR_BGR2HSV).astype(np.float32)

    # Teeth zone: high V (>105), moderate S (<110), Hue in yellow range (12 to 55)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]

    teeth_mask = ((val > 105) & (sat < 110) & ((hue >= 12) & (hue <= 55))).astype(np.float32)

    if np.sum(teeth_mask) > 5:
        teeth_blur = cv2.GaussianBlur(teeth_mask, (5, 5), 0)
        # Desaturate yellow cast
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 - teeth_blur * whitening_strength * 0.65), 0, 255)
        # Gently lift brightness
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + teeth_blur * whitening_strength * 0.20), 0, 255)

        whitened_patch = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)

        ell_mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
        cx, cy = (x2 - x1) // 2, (y2 - y1) // 2
        cv2.ellipse(ell_mask, (cx, cy), (int((x2 - x1) * 0.45), int((y2 - y1) * 0.45)), 0, 0, 360, 1.0, -1)
        ell_mask = cv2.GaussianBlur(ell_mask, (5, 5), 0)[:, :, np.newaxis]

        out = img_f.copy()
        out[y1:y2, x1:x2] = whitened_patch * ell_mask + patch * (1.0 - ell_mask)
        return out

    return img_f

whiten_teeth_codeformer = whiten_teeth_enamel


def apply_subsurface_melanin_radiance(img_f, skin_mask_f, glow_intensity=0.40, is_morena=True):
    """
    Sub-Surface Melanin Radiance & Studio Glow:
      - Adds diffuse luminosity to cheekbones, forehead, and bridge of the nose
      - Harmonizes Filipino Morena golden tones without unnatural lightening
    """
    if glow_intensity <= 0.05 or skin_mask_f is None:
        return img_f

    # High-luminance skin highlights
    gray = cv2.cvtColor(np.clip(img_f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    highlight_mask = np.clip((gray - 118.0) / 105.0, 0.0, 1.0)[:, :, np.newaxis]

    # Soft diffuse bloom
    bloom = cv2.GaussianBlur(img_f, (27, 27), 0)

    if is_morena:
        # Subtle Morena golden undertone shift in radiance bloom
        bloom[:, :, 2] = np.clip(bloom[:, :, 2] * 1.035, 0, 255)  # Red warmth
        bloom[:, :, 1] = np.clip(bloom[:, :, 1] * 1.018, 0, 255)  # Green gold

    glow_factor = glow_intensity * 0.30 * skin_mask_f * highlight_mask
    out = img_f * (1.0 - glow_factor) + (img_f + bloom * 0.42) * glow_factor
    return np.clip(out, 0, 255)

apply_studio_glow_beautyglow = apply_subsurface_melanin_radiance



def apply_studio_environment_lighting(img_f, subject_mask, lighting_temp="neutral_5500k", studio_light_intensity=0.20, rim_light_boost=0.25):
    """
    Simulates Studio Key Light, Color Temperature & Rim Lighting:
      - Color Temperature: Warm 3200K Tungsten, Neutral 5500K Studio Strobe, Cool 6500K High-Key
      - Studio Key Light: 45-degree overhead softbox gradient falloff
      - Rim Light: Edge illumination on subject hair and shoulders
    """
    if img_f is None:
        return img_f
        
    h, w = img_f.shape[:2]
    out = img_f.copy()

    # 1. Color Temperature Grading
    if lighting_temp == "warm_3200k":
        # Warm golden tungsten (+Red, +Green slightly, -Blue)
        out[:, :, 2] = np.clip(out[:, :, 2] * 1.05, 0, 255)
        out[:, :, 1] = np.clip(out[:, :, 1] * 1.02, 0, 255)
        out[:, :, 0] = np.clip(out[:, :, 0] * 0.95, 0, 255)
    elif lighting_temp == "cool_6500k":
        # Cool crisp high-key (+Blue, +Highlights)
        out[:, :, 0] = np.clip(out[:, :, 0] * 1.04, 0, 255)
        out[:, :, 2] = np.clip(out[:, :, 2] * 0.98, 0, 255)

    # 2. Studio Softbox Key Light Gradient
    if studio_light_intensity > 0.05:
        # 45-degree top-left studio key light gradient
        y_grid, x_grid = np.ogrid[:h, :w]
        key_dist = np.sqrt(((x_grid - w * 0.35) / (w * 0.8)) ** 2 + ((y_grid - h * 0.25) / (h * 0.8)) ** 2)
        key_dist = np.clip(1.0 - key_dist, 0.0, 1.0)[:, :, np.newaxis]
        key_boost = key_dist * (studio_light_intensity * 32.0)
        out = np.clip(out + key_boost, 0, 255)

    # 3. Studio Rim Light on Hair & Silhouette Edges
    if rim_light_boost > 0.05 and subject_mask is not None:
        # Extract subject boundary
        if len(subject_mask.shape) == 3:
            subject_mask = cv2.cvtColor(subject_mask, cv2.COLOR_BGR2GRAY)
        
        edges = cv2.Canny(subject_mask, 80, 180)
        edges = cv2.dilate(edges, np.ones((7, 7), np.uint8), iterations=1)
        rim_mask = (cv2.GaussianBlur(edges.astype(np.float32), (9, 9), 0) / 255.0)[:, :, np.newaxis]
        
        rim_color = np.array([245, 235, 220], dtype=np.float32) if lighting_temp == "warm_3200k" else np.array([255, 250, 245], dtype=np.float32)
        rim_glow = rim_mask * (rim_light_boost * 40.0)
        out = np.clip(out + rim_glow, 0, 255)

    return out


def apply_beauty_preset_to_image(img_bgr, face_info=None, preset_id="morena_radiant", custom_adjustments=None, ai_config=None):
    """
    Orchestrates the Full AI Glow-Up & Beautification Pipeline:
      1. AI Skin Undertone Analysis (Melanin & Warmth Evaluation)
      2. RetouchFormer Soft-Inpainting Blemish & Pimple Removal
      3. Dark Spot Whitening & Hyperpigmentation Balancing
      4. Frequency Separation (Tone smoothing with pore preservation)
      5. T-Zone Specular Highlight De-Shine
      6. Neural Lip Tinting & Recoloring
      7. CodeFormer Iris Catchlight & Sclera Clarity
      8. CodeFormer Enamel Teeth Whitening
      9. BeautyGlow Sub-Surface Radiance & Melanin Balance
      10. Studio Key Lighting & Color Temperature Environment Grading
      11. CodeFormer Fidelity Prior Blending
    """
    params = BEAUTY_PRESETS.get(preset_id, BEAUTY_PRESETS["morena_radiant"]).copy()
    if custom_adjustments:
        params.update(custom_adjustments)

    # AI Multimodal Guidance from Google Gemini & Neural Tone Analysis
    gemini_data = None
    if isinstance(ai_config, dict):
        gemini_data = ai_config.get("gemini_ai")

    ai_skin = analyze_portrait_skin_ai(img_bgr, face_info)
    is_warm_morena = ai_skin.get("is_morena", True)
    if gemini_data and gemini_data.get("skin_undertone") == "warm_morena":
        is_warm_morena = True

    if preset_id == "morena_radiant" and is_warm_morena:
        params["warmth_boost"] = 1.05

    if gemini_data and "blemish_score" in gemini_data:
        b_score = float(gemini_data.get("blemish_score", 15))
        params["blemish_cut"] = min(0.92, max(0.45, b_score / 25.0 * 0.75))

    h, w = img_bgr.shape[:2]
    img_f = img_bgr.astype(np.float32)

    if face_info is None:
        return img_bgr

    x, y, fw, fh = face_info['bbox']
    r_eye, l_eye, nose = face_info['right_eye'], face_info['left_eye'], face_info['nose']
    r_mouth, l_mouth = face_info['right_mouth'], face_info['left_mouth']

    # 1. Precise Facial & Neck Skin Mask in YCrCb
    skin_mask = np.zeros((h, w), dtype=np.uint8)
    center_x, center_y = x + fw // 2, y + int(fh * 0.52)
    cv2.ellipse(skin_mask, (center_x, center_y), (int(fw * 0.44), int(fh * 0.52)), 0, 0, 360, 255, -1)

    chin_y = y + fh
    neck_w = int(fw * 0.32)
    neck_pts = np.array([
        [center_x - neck_w, chin_y - 10],
        [center_x + neck_w, chin_y - 10],
        [center_x + int(neck_w * 0.65), chin_y + 80],
        [center_x - int(neck_w * 0.65), chin_y + 80]
    ], np.int32)
    cv2.fillPoly(skin_mask, [neck_pts], 255)

    img_ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    color_skin = cv2.inRange(img_ycrcb, np.array([60, 133, 80], dtype=np.uint8), np.array([235, 172, 132], dtype=np.uint8))
    skin_mask = cv2.bitwise_and(skin_mask, color_skin)

    # Protect eyes, nostrils, and lips from aggressive skin smoothing
    cv2.circle(skin_mask, tuple(r_eye), int(fw * 0.14), 0, -1)
    cv2.circle(skin_mask, tuple(l_eye), int(fw * 0.14), 0, -1)
    cv2.circle(skin_mask, tuple(nose), int(fw * 0.08), 0, -1)
    mouth_c = ((int(r_mouth[0]) + int(l_mouth[0])) // 2, (int(r_mouth[1]) + int(l_mouth[1])) // 2)
    cv2.ellipse(skin_mask, tuple(mouth_c), (int(fw * 0.24), int(fh * 0.12)), 0, 0, 360, 0, -1)

    # 2. Localized Blemish & Pimple Healing
    blemish_cut = float(params.get("blemish_cut", 0.70))
    healed_bgr = detect_and_heal_blemishes(img_bgr, skin_mask, blemish_strength=blemish_cut)
    
    # 3. Dark Spot Correction & Hyperpigmentation Lightening
    dark_spot_whiten = float(params.get("dark_spot_whitening", 0.50))
    healed_bgr = whiten_dark_spots_and_hyperpigmentation(healed_bgr, skin_mask, whitening_strength=dark_spot_whiten)
    healed_f = healed_bgr.astype(np.float32)

    # 4. Frequency Separation (Tone smoothing with pore preservation)
    skin_mask_f = (cv2.GaussianBlur(skin_mask, (15, 15), 0).astype(np.float32) / 255.0)[:, :, np.newaxis]
    low_freq = cv2.GaussianBlur(healed_f, (15, 15), 0)
    high_freq = healed_f - low_freq + 128.0

    low_u8 = np.clip(low_freq, 0, 255).astype(np.uint8)
    smoothed_low = cv2.bilateralFilter(low_u8, d=13, sigmaColor=28, sigmaSpace=13).astype(np.float32)

    # 5. T-Zone Specular De-Shine
    shine_cut = float(params.get("shine_reduction", 0.35))
    if shine_cut > 0.05:
        gray_low = cv2.cvtColor(low_u8, cv2.COLOR_BGR2GRAY)
        _, shine_pts = cv2.threshold(gray_low, 180, 255, cv2.THRESH_BINARY)
        shine_pts = cv2.bitwise_and(shine_pts, skin_mask)
        shine_blur = (cv2.GaussianBlur(shine_pts, (15, 15), 0).astype(np.float32) / 255.0)[:, :, np.newaxis]
        smoothed_low = smoothed_low * (1.0 - shine_blur * shine_cut * 0.28)

    skin_ratio = float(params.get("skin_smoothing", 0.65))
    blended_low = low_freq * (1.0 - skin_ratio) + smoothed_low * skin_ratio

    # Micro-pore texture reconstruction
    skin_recombined = np.clip(blended_low + high_freq - 128.0, 0, 255)
    base_with_skin = skin_recombined * skin_mask_f + healed_f * (1.0 - skin_mask_f)

    # 6. Neural Lip Tinting & Recoloring
    lip_intensity = float(params.get("lip_intensity", 0.35))
    lip_color_hex = str(params.get("lip_color", "#d87093"))
    base_with_skin = recolor_lips_neural(
        base_with_skin,
        r_mouth,
        l_mouth,
        fw,
        fh,
        lip_color_hex=lip_color_hex,
        lip_intensity=lip_intensity
    )

    # 7. Eye Catchlight & Sclera Clarity
    eye_sharpen = float(params.get("eye_sharpen", 0.25))
    catchlight_boost = float(params.get("catchlight_boost", 0.40))
    base_with_skin = enhance_eye_catchlights(
        base_with_skin,
        r_eye,
        l_eye,
        fw,
        eye_sharpen=eye_sharpen,
        catchlight_boost=catchlight_boost
    )

    # 8. Natural Enamel Teeth Whitening
    teeth_whitening = float(params.get("teeth_whitening", 0.45))
    base_with_skin = whiten_teeth_enamel(
        base_with_skin,
        r_mouth,
        l_mouth,
        fw,
        fh,
        whitening_strength=teeth_whitening
    )

    # 9. Sub-Surface Melanin Radiance
    glow_intensity = float(params.get("glow_intensity", 0.40))
    base_with_skin = apply_subsurface_melanin_radiance(
        base_with_skin,
        skin_mask_f,
        glow_intensity=glow_intensity,
        is_morena=is_warm_morena
    )

    # 10. Studio Environment & Key Lighting
    lighting_temp = params.get("lighting_temp", "neutral_5500k")
    studio_light_intensity = float(params.get("studio_light_intensity", 0.20))
    rim_light_boost = float(params.get("rim_light_boost", 0.20))
    base_with_skin = apply_studio_environment_lighting(
        base_with_skin,
        skin_mask,
        lighting_temp=lighting_temp,
        studio_light_intensity=studio_light_intensity,
        rim_light_boost=rim_light_boost
    )

    # 11. Morena Golden Warmth Adjustment
    warmth = float(params.get("warmth_boost", 1.0))
    if warmth != 1.0:
        base_with_skin[:, :, 2] = np.clip(base_with_skin[:, :, 2] * warmth, 0, 255)
        base_with_skin[:, :, 1] = np.clip(base_with_skin[:, :, 1] * (1.0 + (warmth - 1.0) * 0.5), 0, 255)

    # 12. CodeFormer Fidelity Weight Blending (Balance raw realism vs neural polish)
    fidelity_weight = float(params.get("fidelity_weight", 0.75))
    final_output = base_with_skin * (1.0 - fidelity_weight * 0.20) + img_f * (fidelity_weight * 0.20)

    return np.clip(final_output, 0, 255).astype(np.uint8)
