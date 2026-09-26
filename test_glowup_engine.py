import cv2
import numpy as np
import os
import time

def get_face_landmarks(img, w, h):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.environ.get("YUNET_MODEL_PATH", os.path.join(base_dir, "face_detection_yunet.onnx"))
    if not os.path.exists(model_path):
        return None
    try:
        detector = cv2.FaceDetectorYN_create(model_path, '', (w, h), 0.7, 0.3, 5000)
        detector.setInputSize((w, h))
        _, faces = detector.detect(img)
        if faces is not None and len(faces) > 0:
            f = faces[0]
            return {
                "bbox": f[:4].astype(int).tolist(),
                "right_eye": f[4:6].astype(int).tolist(),
                "left_eye": f[6:8].astype(int).tolist(),
                "nose": f[8:10].astype(int).tolist(),
                "right_mouth": f[10:12].astype(int).tolist(),
                "left_mouth": f[12:14].astype(int).tolist()
            }
    except Exception as e:
        print("Error detecting face:", e)
    return None

def detect_and_heal_blemishes(img_bgr, skin_mask, blemish_strength=0.75):
    """
    RetouchFormer-style localized blemish & acne healing with pore preservation.
    Uses Difference of Gaussians (DoG) on luminance to locate localized imperfections,
    then applies soft neural inpainting only onto the blemish centroids.
    """
    if blemish_strength <= 0.05 or skin_mask is None:
        return img_bgr
        
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.float32)
    
    # Difference of Gaussians to isolate blemish-scale dark spots
    g1 = cv2.GaussianBlur(L, (3, 3), 1.0)
    g2 = cv2.GaussianBlur(L, (11, 11), 3.0)
    dog = g1 - g2
    
    # Blemishes are localized negative spikes relative to surrounding skin
    threshold = -10.0 * (1.2 - blemish_strength * 0.4)
    blemish_mask = ((dog < threshold) & (skin_mask > 128)).astype(np.uint8) * 255
    
    # Remove tiny isolated pixels (keep real pore grain)
    kernel_clean = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    blemish_mask = cv2.morphologyEx(blemish_mask, cv2.MORPH_OPEN, kernel_clean)
    blemish_mask = cv2.dilate(blemish_mask, kernel_clean, iterations=1)
    
    if cv2.countNonZero(blemish_mask) > 0:
        # Soft inpaint on blemish clusters using Navier-Stokes
        inpainted = cv2.inpaint(img_bgr, blemish_mask, inpaintRadius=3, flags=cv2.INPAINT_NS)
        
        # Soft-blend inpainting with original to preserve skin texture
        mask_f = (cv2.GaussianBlur(blemish_mask, (5, 5), 0).astype(np.float32) / 255.0 * blemish_strength)[:, :, np.newaxis]
        healed = (inpainted.astype(np.float32) * mask_f + img_bgr.astype(np.float32) * (1.0 - mask_f))
        return np.clip(healed, 0, 255).astype(np.uint8)
        
    return img_bgr

def enhance_eye_catchlights_and_sclera(img_f, r_eye, l_eye, fw, eye_sharpen=0.35, catchlight_boost=0.45):
    """
    CodeFormer-style eye iris radiance and catchlight enhancement:
      - Desaturates bloodshot redness in eye sclera (clean eye whites)
      - Sharpens iris limbal ring
      - Amplifies pupil specular catchlights from studio strobes
    """
    h, w = img_f.shape[:2]
    eye_radius_x = int(fw * 0.12)
    eye_radius_y = int(fw * 0.08)
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
        
        # 1. Sclera (Eye Whites): High V, Low S in non-pupil region
        sclera_mask = ((v > 120) & (s < 120)).astype(np.float32)
        # Gently desaturate bloodshot veins and brighten
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 - sclera_mask * 0.40), 0, 255)
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + sclera_mask * 0.08), 0, 255)
        
        # 2. Specular Catchlight in Pupil: Brightest glint pixels (v > 200)
        catchlight_mask = (v > 195).astype(np.float32)
        if np.sum(catchlight_mask) > 0 and catchlight_boost > 0.05:
            catchlight_blur = cv2.GaussianBlur(catchlight_mask, (3, 3), 0)
            hsv[:, :, 2] = np.clip(hsv[:, :, 2] + catchlight_blur * (catchlight_boost * 45.0), 0, 255)
            
        enhanced_patch = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        
        # 3. Iris Sharpening
        if eye_sharpen > 0.05:
            blurred_patch = cv2.GaussianBlur(enhanced_patch, (0, 0), 2.0)
            enhanced_patch = cv2.addWeighted(enhanced_patch, 1.0 + eye_sharpen * 0.7, blurred_patch, -eye_sharpen * 0.7, 0)
            
        # Smoothly feather into eye region
        ell_mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
        cx, cy = (x2 - x1) // 2, (y2 - y1) // 2
        cv2.ellipse(ell_mask, (cx, cy), (int((x2 - x1) * 0.46), int((y2 - y1) * 0.46)), 0, 0, 360, 1.0, -1)
        ell_mask = cv2.GaussianBlur(ell_mask, (5, 5), 0)[:, :, np.newaxis]
        
        out[y1:y2, x1:x2] = enhanced_patch * ell_mask + patch * (1.0 - ell_mask)
        
    return out

def whiten_teeth_naturally(img_f, r_mouth, l_mouth, fw, fh, whitening_strength=0.50):
    """
    CodeFormer-style natural teeth whitening & enamel brightening:
      - Targets mouth aperture between mouth corners
      - Selectively targets yellow/dull tint without bleaching lips
    """
    if whitening_strength <= 0.05:
        return img_f
        
    h, w = img_f.shape[:2]
    mx = (int(r_mouth[0]) + int(l_mouth[0])) // 2
    my = (int(r_mouth[1]) + int(l_mouth[1])) // 2
    
    mw = int(abs(l_mouth[0] - r_mouth[0]) * 0.8)
    mh = int(fh * 0.15)
    
    x1, x2 = max(0, mx - mw // 2), min(w, mx + mw // 2)
    y1, y2 = max(0, my - mh // 2), min(h, my + mh // 2)
    
    patch = img_f[y1:y2, x1:x2]
    if patch.size == 0:
        return img_f
        
    patch_u8 = np.clip(patch, 0, 255).astype(np.uint8)
    hsv = cv2.cvtColor(patch_u8, cv2.COLOR_BGR2HSV).astype(np.float32)
    
    # Teeth region: high V (>110), moderate S (<120), Hue in yellow-neutral range (15 to 45)
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    
    teeth_mask = ((val > 105) & (sat < 110) & ((hue >= 12) & (hue <= 55))).astype(np.float32)
    
    if np.sum(teeth_mask) > 5:
        teeth_blur = cv2.GaussianBlur(teeth_mask, (5, 5), 0)
        # Desaturate yellow cast
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1.0 - teeth_blur * whitening_strength * 0.65), 0, 255)
        # Brighten enamel
        hsv[:, :, 2] = np.clip(hsv[:, :, 2] * (1.0 + teeth_blur * whitening_strength * 0.22), 0, 255)
        
        whitened_patch = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
        
        ell_mask = np.zeros((y2 - y1, x2 - x1), dtype=np.float32)
        cx, cy = (x2 - x1) // 2, (y2 - y1) // 2
        cv2.ellipse(ell_mask, (cx, cy), (int((x2 - x1) * 0.44), int((y2 - y1) * 0.44)), 0, 0, 360, 1.0, -1)
        ell_mask = cv2.GaussianBlur(ell_mask, (5, 5), 0)[:, :, np.newaxis]
        
        out = img_f.copy()
        out[y1:y2, x1:x2] = whitened_patch * ell_mask + patch * (1.0 - ell_mask)
        return out
        
    return img_f

def apply_studio_glow_radiance(img_f, skin_mask_f, glow_intensity=0.40, is_morena=True):
    """
    BeautyGlow-style sub-surface skin radiance & golden glow:
      - Adds diffuse luminosity to cheekbones and forehead
      - Infuses warm Filipino Morena golden tones
    """
    if glow_intensity <= 0.05 or skin_mask_f is None:
        return img_f
        
    # High-luminance skin highlights
    gray = cv2.cvtColor(np.clip(img_f, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
    highlight_mask = np.clip((gray - 120.0) / 100.0, 0.0, 1.0)[:, :, np.newaxis]
    
    # Soft diffuse bloom
    bloom = cv2.GaussianBlur(img_f, (27, 27), 0)
    
    if is_morena:
        # Subtle Morena golden undertone shift in bloom
        bloom[:, :, 2] = np.clip(bloom[:, :, 2] * 1.035, 0, 255) # Red/warmth
        bloom[:, :, 1] = np.clip(bloom[:, :, 1] * 1.018, 0, 255) # Green/gold
        
    glow_factor = glow_intensity * 0.32 * skin_mask_f * highlight_mask
    out = img_f * (1.0 - glow_factor) + (img_f + bloom * 0.45) * glow_factor
    return np.clip(out, 0, 255)

if __name__ == '__main__':
    print("Glow-up functions defined successfully!")
    if os.path.exists("sample_grad.jpg"):
        img = cv2.imread("sample_grad.jpg")
        if img is not None:
            h, w = img.shape[:2]
            face_info = get_face_landmarks(img, w, h)
            if face_info:
                print("Face info:", face_info['bbox'])

                start = time.time()
                # Step 1: Skin mask
                x, y, fw, fh = face_info['bbox']
                skin_mask = np.zeros((h, w), dtype=np.uint8)
                cx, cy = x + fw // 2, y + int(fh * 0.52)
                cv2.ellipse(skin_mask, (cx, cy), (int(fw * 0.44), int(fh * 0.52)), 0, 0, 360, 255, -1)
                img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
                color_skin = cv2.inRange(img_ycrcb, np.array([60, 133, 80], dtype=np.uint8), np.array([235, 172, 132], dtype=np.uint8))
                skin_mask = cv2.bitwise_and(skin_mask, color_skin)

                # Test Blemish Healing
                healed = detect_and_heal_blemishes(img, skin_mask, blemish_strength=0.80)

                # Test Eye Catchlights
                healed_f = healed.astype(np.float32)
                eyes_enhanced = enhance_eye_catchlights_and_sclera(
                    healed_f,
                    face_info['right_eye'],
                    face_info['left_eye'],
                    fw,
                    eye_sharpen=0.40,
                    catchlight_boost=0.50
                )

                # Test Teeth Whitening
                teeth_whitened = whiten_teeth_naturally(
                    eyes_enhanced,
                    face_info['right_mouth'],
                    face_info['left_mouth'],
                    fw,
                    fh,
                    whitening_strength=0.60
                )

                # Test Studio Radiance Glow
                skin_mask_f = (cv2.GaussianBlur(skin_mask, (15, 15), 0).astype(np.float32) / 255.0)[:, :, np.newaxis]
                glowing = apply_studio_glow_radiance(teeth_whitened, skin_mask_f, glow_intensity=0.45, is_morena=True)
                final_result = np.clip(glowing, 0, 255).astype(np.uint8)

                elapsed = (time.time() - start) * 1000
                print(f"Glow-up complete in {elapsed:.1f}ms!")
                cv2.imwrite("test_glowup_result.jpg", final_result)
                print("Saved test_glowup_result.jpg successfully!")
