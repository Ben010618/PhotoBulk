import cv2
import numpy as np
import os

STUDIO_BACKDROPS = {
    "royal_navy": {
        "id": "royal_navy",
        "name": "Signature Royal Navy & Cobalt Muslin",
        "description": "The standard academic palette used by major Philippine graduation studios (AuraGrad, Lumina Academic, and classic Manila studios).",
        "hex": "#122a4d",
        "file": "studio_backdrop_royal_navy.jpg"
    },
    "warm_amber": {
        "id": "warm_amber",
        "name": "Warm Amber Radial Strobe Spotlight",
        "description": "Replicates a 45-degree overhead studio key-light to naturally backlight the student's head and graduation cap.",
        "hex": "#b8864a",
        "file": "studio_backdrop_warm_amber.jpg"
    },
    "organic_texture": {
        "id": "organic_texture",
        "name": "Organic Hand-Painted Texture",
        "description": "Eliminates synthetic solid digital color, providing depth and authentic painted canvas brushstrokes.",
        "hex": "#4a5359",
        "file": "studio_backdrop_organic_texture.jpg"
    },
    "prc_red": {
        "id": "prc_red",
        "name": "PRC Crimson",
        "description": "Official Philippine Professional Regulation Commission (PRC) Board Exam crimson red background.",
        "hex": "#8a141b",
        "file": None
    },
    "studio_white": {
        "id": "studio_white",
        "name": "Studio Pure White (Formal / Passport)",
        "description": "Crisp high-key pure white studio seamless background for passports and formal archives.",
        "hex": "#f5f6f8",
        "file": None
    },
    "slate_gray": {
        "id": "slate_gray",
        "name": "Minimalist Slate Gray",
        "description": "Contemporary editorial neutral slate gray with subtle radial center lighting falloff.",
        "hex": "#3b4252",
        "file": None
    }
}

def generate_studio_backdrop(width, height, backdrop_type="royal_navy", custom_img_bgr=None):
    """
    Renders or loads high-resolution authentic Philippine studio backdrops:
      - 'royal_navy': Signature Royal Navy & Cobalt Muslin
      - 'warm_amber': Warm Amber Radial Strobe Spotlight
      - 'organic_texture': Organic Hand-Painted Texture
      - 'prc_red': PRC Crimson
      - 'studio_white': Studio Pure White
      - 'slate_gray': Minimalist Slate Gray
      - 'custom': User-uploaded studio canvas
    """
    # 1. Custom backdrop
    if backdrop_type == "custom" and custom_img_bgr is not None:
        return cv2.resize(custom_img_bgr, (width, height), interpolation=cv2.INTER_LANCZOS4)
        
    # Backward compatibility mapping
    if backdrop_type == "mottled_navy":
        backdrop_type = "royal_navy"
        
    info = STUDIO_BACKDROPS.get(backdrop_type, STUDIO_BACKDROPS["royal_navy"])
    
    # 2. Check if pre-rendered image asset exists
    if info.get("file") and os.path.exists(info["file"]):
        loaded_bg = cv2.imread(info["file"])
        if loaded_bg is not None:
            return cv2.resize(loaded_bg, (width, height), interpolation=cv2.INTER_LANCZOS4)
            
    # 3. Dynamic synthesis fallback
    bg = np.zeros((height, width, 3), dtype=np.uint8)
    
    if backdrop_type == "prc_red":
        # PRC Crimson gradient
        y, x = np.ogrid[:height, :width]
        cx, cy = width / 2.0, height * 0.42
        dist = np.sqrt(((x - cx) / (width * 0.72)) ** 2 + ((y - cy) / (height * 0.72)) ** 2)
        dist = np.clip(dist, 0.0, 1.0)
        
        b = (30 * (1 - dist) + 12 * dist).astype(np.uint8)
        g = (20 * (1 - dist) + 8 * dist).astype(np.uint8)
        r = (185 * (1 - dist) + 95 * dist).astype(np.uint8)
        return cv2.merge([b, g, r])
        
    elif backdrop_type == "warm_amber":
        # Warm Amber Radial Strobe Spotlight fallback
        y, x = np.ogrid[:height, :width]
        cx, cy = width / 2.0, height * 0.40
        dist = np.sqrt(((x - cx) / (width * 0.65)) ** 2 + ((y - cy) / (height * 0.65)) ** 2)
        dist = np.clip(dist, 0.0, 1.0)
        
        b = (70 * (1 - dist) + 20 * dist).astype(np.uint8)
        g = (150 * (1 - dist) + 25 * dist).astype(np.uint8)
        r = (215 * (1 - dist) + 35 * dist).astype(np.uint8)
        return cv2.merge([b, g, r])
        
    elif backdrop_type == "organic_texture":
        # Organic Muted Hand-Painted Canvas fallback
        y, x = np.ogrid[:height, :width]
        cx, cy = width / 2.0, height * 0.42
        dist = np.sqrt(((x - cx) / (width * 0.70)) ** 2 + ((y - cy) / (height * 0.70)) ** 2)
        dist = np.clip(dist, 0.0, 1.0)
        
        gray_val = (160 * (1 - dist) + 55 * dist).astype(np.uint8)
        bg = cv2.merge([gray_val, gray_val, gray_val])
        return bg

    elif backdrop_type == "studio_white":
        # Pure studio white with subtle soft vignette at edges
        y, x = np.ogrid[:height, :width]
        cx, cy = width / 2.0, height * 0.40
        dist = np.sqrt(((x - cx) / (width * 0.85)) ** 2 + ((y - cy) / (height * 0.85)) ** 2)
        dist = np.clip(dist, 0.0, 1.0)
        val = (252 * (1 - dist) + 236 * dist).astype(np.uint8)
        return cv2.merge([val, val, val])

    elif backdrop_type == "slate_gray":
        # Slate gray with soft strobe center
        y, x = np.ogrid[:height, :width]
        cx, cy = width / 2.0, height * 0.40
        dist = np.sqrt(((x - cx) / (width * 0.70)) ** 2 + ((y - cy) / (height * 0.70)) ** 2)
        dist = np.clip(dist, 0.0, 1.0)
        b = (100 * (1 - dist) + 45 * dist).astype(np.uint8)
        g = (85 * (1 - dist) + 40 * dist).astype(np.uint8)
        r = (75 * (1 - dist) + 35 * dist).astype(np.uint8)
        return cv2.merge([b, g, r])
        
    else: # Default: 'royal_navy'
        # Royal Navy & Cobalt Muslin fallback
        y, x = np.ogrid[:height, :width]
        cx, cy = width / 2.0, height * 0.40
        dist = np.sqrt(((x - cx) / (width * 0.70)) ** 2 + ((y - cy) / (height * 0.70)) ** 2)
        dist = np.clip(dist, 0.0, 1.0)
        
        b = (165 * (1 - dist) + 65 * dist).astype(np.uint8)
        g = (75 * (1 - dist) + 25 * dist).astype(np.uint8)
        r = (30 * (1 - dist) + 10 * dist).astype(np.uint8)
        return cv2.merge([b, g, r])

def composite_subject_onto_backdrop(subject_bgr, alpha_mask, backdrop_bgr, edge_feather_px=3):
    """
    Composites foreground subject onto the new studio backdrop with:
      1. Edge feathering to eliminate jagged cutouts.
      2. Color de-spill around hair and shoulders to remove ambient background bleed.
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
        
    alpha_norm = (alpha_feathered.astype(np.float32) / 255.0)[:, :, np.newaxis]
    
    # Despill: suppress harsh edge bounce from previous background
    edge_zone = cv2.Canny(alpha_mask, 100, 200)
    edge_zone = cv2.dilate(edge_zone, np.ones((5, 5), np.uint8), iterations=1)
    edge_mask = (edge_zone > 0)[:, :, np.newaxis]
    
    subj_f = subject_bgr.astype(np.float32)
    bg_f = bg_resized.astype(np.float32)
    
    subj_despilled = np.where(edge_mask, subj_f * 0.90 + bg_f * 0.10, subj_f)
    
    composited = subj_despilled * alpha_norm + bg_f * (1.0 - alpha_norm)
    return np.clip(composited, 0, 255).astype(np.uint8)
