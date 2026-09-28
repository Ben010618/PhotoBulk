"""
KameraPh Face Parsing & Semantic Anatomy Mask Engine
---------------------------------------------------
Generates high-precision semantic segmentation masks for portrait retouching:
  - 'skin': facial skin and neck (excluding eyes, brows, lips)
  - 'hair': head hair silhouette
  - 'eyes': left and right eye orbs and irises
  - 'brows': left and right eyebrows
  - 'lips': upper and lower lips
  - 'neck': anatomical neck region
  - 'hat': graduation cap / mortarboard
  - 'cloth': graduation toga, barong, sablay, or formal attire

Uses BiSeNet ONNX model (53MB) with robust anatomical landmark fallbacks.
"""

import os
import cv2
import numpy as np
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("kameraph.face_parsing")

BASE_DIR = Path(__file__).resolve().parent
BISENET_MODEL_PATH = BASE_DIR / "bisenet_face_parsing.onnx"
_PARSER_SESSION = None


def has_bisenet_model() -> bool:
    """Returns True if the BiSeNet ONNX model weight file is present on disk."""
    return BISENET_MODEL_PATH.is_file()


def get_parsing_session():
    """Initializes or returns cached onnxruntime session for BiSeNet face parsing."""
    global _PARSER_SESSION
    if _PARSER_SESSION is not None:
        return _PARSER_SESSION

    if not has_bisenet_model():
        logger.info(
            "BiSeNet face parsing model not found at %s. Geometric anatomical fallback is active.",
            BISENET_MODEL_PATH
        )
        return None

    try:
        import onnxruntime as ort
        _PARSER_SESSION = ort.InferenceSession(str(BISENET_MODEL_PATH), providers=['CPUExecutionProvider'])
        logger.info("Initialized BiSeNet Face Parsing ONNX session.")
        return _PARSER_SESSION
    except Exception as e:
        logger.warning(f"Could not initialize BiSeNet session: {e}. Falling back to geometric masks.")
        return None


def get_face_parsing_masks(
    img_bgr: np.ndarray,
    face_info: Optional[Dict[str, Any]] = None
) -> Dict[str, np.ndarray]:
    """
    Computes exact semantic parsing masks for portrait beauty and lighting.
    Returns dict of uint8 masks (0-255) matching the input image shape (H, W):
      - 'skin', 'hair', 'eyes', 'brows', 'lips', 'neck', 'hat', 'cloth'
    """
    h, w = img_bgr.shape[:2]
    session = get_parsing_session()

    if session is not None:
        try:
            rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, (512, 512)).astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            norm = (resized - mean) / std
            blob = norm.transpose(2, 0, 1)[np.newaxis, ...]

            out = session.run(['output'], {'input': blob})[0]
            preds_512 = np.argmax(out[0], axis=0).astype(np.uint8)
            preds = cv2.resize(preds_512, (w, h), interpolation=cv2.INTER_NEAREST)

            # CelebAMask-HQ class mapping:
            # 1: skin, 2: l_brow, 3: r_brow, 4: l_eye, 5: r_eye, 10: nose, 11: mouth, 12: u_lip, 13: l_lip, 14: neck, 16: cloth, 17: hair, 18: hat
            skin_raw = np.isin(preds, [1, 10]).astype(np.uint8) * 255
            neck_raw = (preds == 14).astype(np.uint8) * 255
            hair_raw = (preds == 17).astype(np.uint8) * 255
            eyes_raw = np.isin(preds, [4, 5]).astype(np.uint8) * 255
            brows_raw = np.isin(preds, [2, 3]).astype(np.uint8) * 255
            lips_raw = np.isin(preds, [11, 12, 13]).astype(np.uint8) * 255
            hat_raw = (preds == 18).astype(np.uint8) * 255
            cloth_raw = (preds == 16).astype(np.uint8) * 255
            mouth_raw = (preds == 11).astype(np.uint8) * 255
            ears_raw = np.isin(preds, [7, 8]).astype(np.uint8) * 255

            # Fallback to landmarks if specific small facial features are missing
            if face_info and 'bbox' in face_info:
                geom = _build_geometric_parsing_masks(img_bgr, face_info)
                if cv2.countNonZero(eyes_raw) == 0:
                    eyes_raw = geom["eyes"]
                if cv2.countNonZero(brows_raw) == 0:
                    brows_raw = geom["brows"]
                if cv2.countNonZero(lips_raw) == 0:
                    lips_raw = geom["lips"]

            # Exclude eyes, brows, and lips from skin mask so they are never smoothed or bleached
            features_to_cut = cv2.bitwise_or(eyes_raw, brows_raw)
            features_to_cut = cv2.bitwise_or(features_to_cut, lips_raw)
            skin_raw = cv2.bitwise_and(skin_raw, cv2.bitwise_not(features_to_cut))

            # Combine face skin and neck for unified skin smoothing
            full_skin = cv2.bitwise_or(skin_raw, neck_raw)

            return {
                "skin": full_skin,
                "facial_skin": skin_raw,
                "hair": hair_raw,
                "eyes": eyes_raw,
                "brows": brows_raw,
                "lips": lips_raw,
                "neck": neck_raw,
                "hat": hat_raw,
                "cloth": cloth_raw,
                "mouth": mouth_raw,
                "ears": ears_raw
            }
        except Exception as e:
            logger.warning(f"BiSeNet parsing inference failed: {e}. Falling back to geometric masks.")

    # High-precision anatomical geometric fallback using YuNet landmarks
    logger.info("BiSeNet model inactive or unavailable; anatomical geometric fallback is active.")
    return _build_geometric_parsing_masks(img_bgr, face_info)


def _build_geometric_parsing_masks(
    img_bgr: np.ndarray,
    face_info: Optional[Dict[str, Any]] = None
) -> Dict[str, np.ndarray]:
    """Generates clean landmark-aligned anatomical masks when ONNX model is absent."""
    h, w = img_bgr.shape[:2]
    empty = np.zeros((h, w), dtype=np.uint8)

    if face_info is None or 'bbox' not in face_info:
        # Safe default full-frame mask
        return {
            "skin": empty, "facial_skin": empty, "hair": empty,
            "eyes": empty, "brows": empty, "lips": empty,
            "neck": empty, "hat": empty, "cloth": empty
        }

    fx, fy, fw, fh = int(face_info['bbox'][0]), int(face_info['bbox'][1]), int(face_info['bbox'][2]), int(face_info['bbox'][3])
    r_eye_raw = face_info.get('right_eye')
    r_eye = (int(r_eye_raw[0]), int(r_eye_raw[1])) if r_eye_raw else (int(fx + fw * 0.3), int(fy + fh * 0.35))
    l_eye_raw = face_info.get('left_eye')
    l_eye = (int(l_eye_raw[0]), int(l_eye_raw[1])) if l_eye_raw else (int(fx + fw * 0.7), int(fy + fh * 0.35))
    nose_raw = face_info.get('nose')
    nose = (int(nose_raw[0]), int(nose_raw[1])) if nose_raw else (int(fx + fw * 0.5), int(fy + fh * 0.55))
    r_mouth_raw = face_info.get('right_mouth')
    r_mouth = (int(r_mouth_raw[0]), int(r_mouth_raw[1])) if r_mouth_raw else (int(fx + fw * 0.35), int(fy + fh * 0.75))
    l_mouth_raw = face_info.get('left_mouth')
    l_mouth = (int(l_mouth_raw[0]), int(l_mouth_raw[1])) if l_mouth_raw else (int(fx + fw * 0.65), int(fy + fh * 0.75))

    # 1. Eyes Mask
    eyes_mask = np.zeros((h, w), dtype=np.uint8)
    eye_rx, eye_ry = max(2, int(fw * 0.11)), max(2, int(fh * 0.08))
    cv2.ellipse(eyes_mask, (int(r_eye[0]), int(r_eye[1])), (eye_rx, eye_ry), 0, 0, 360, 255, -1)
    cv2.ellipse(eyes_mask, (int(l_eye[0]), int(l_eye[1])), (eye_rx, eye_ry), 0, 0, 360, 255, -1)

    # 2. Brows Mask
    brows_mask = np.zeros((h, w), dtype=np.uint8)
    brow_offset_y = int(fh * 0.09)
    cv2.ellipse(brows_mask, (int(r_eye[0]), int(r_eye[1] - brow_offset_y)), (max(2, int(eye_rx * 1.2)), max(2, int(eye_ry * 0.6))), -5, 0, 360, 255, -1)
    cv2.ellipse(brows_mask, (int(l_eye[0]), int(l_eye[1] - brow_offset_y)), (max(2, int(eye_rx * 1.2)), max(2, int(eye_ry * 0.6))), 5, 0, 360, 255, -1)

    # 3. Lips Mask
    lips_mask = np.zeros((h, w), dtype=np.uint8)
    mouth_cx = int((r_mouth[0] + l_mouth[0]) / 2.0)
    mouth_cy = int((r_mouth[1] + l_mouth[1]) / 2.0)
    mouth_rx = max(8, int(abs(l_mouth[0] - r_mouth[0]) * 0.65))
    mouth_ry = max(5, int(fh * 0.10))
    cv2.ellipse(lips_mask, (mouth_cx, mouth_cy), (mouth_rx, mouth_ry), 0, 0, 360, 255, -1)

    # 4. Facial Skin & Neck Mask
    skin_mask = np.zeros((h, w), dtype=np.uint8)
    center_x = int(fx + fw // 2)
    center_y = int(fy + fh * 0.52)
    cv2.ellipse(skin_mask, (center_x, center_y), (max(2, int(fw * 0.44)), max(2, int(fh * 0.50))), 0, 0, 360, 255, -1)

    # Neck
    neck_mask = np.zeros((h, w), dtype=np.uint8)
    chin_y = fy + fh
    neck_w = int(fw * 0.32)
    neck_pts = np.array([
        [center_x - neck_w, chin_y - 10],
        [center_x + neck_w, chin_y - 10],
        [center_x + int(neck_w * 0.70), min(h - 1, chin_y + int(fh * 0.40))],
        [center_x - int(neck_w * 0.70), min(h - 1, chin_y + int(fh * 0.40))]
    ], np.int32)
    cv2.fillPoly(neck_mask, [neck_pts], 255)

    # Color thresholding to refine skin to actual human tones
    ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
    color_skin = cv2.inRange(ycrcb, np.array([40, 130, 75], dtype=np.uint8), np.array([245, 175, 135], dtype=np.uint8))
    skin_mask = cv2.bitwise_and(skin_mask, color_skin)
    neck_mask = cv2.bitwise_and(neck_mask, color_skin)

    # Remove eyes, brows, and mouth apertures from skin
    features_to_exclude = cv2.bitwise_or(eyes_mask, brows_mask)
    features_to_exclude = cv2.bitwise_or(features_to_exclude, lips_mask)
    skin_mask = cv2.bitwise_and(skin_mask, cv2.bitwise_not(features_to_exclude))

    full_skin = cv2.bitwise_or(skin_mask, neck_mask)

    # 5. Hat (cap above face) & Hair
    hat_mask = np.zeros((h, w), dtype=np.uint8)
    hair_mask = np.zeros((h, w), dtype=np.uint8)
    cap_top = max(0, fy - int(fh * 0.85))
    cv2.rectangle(hat_mask, (max(0, fx - int(fw * 0.4)), cap_top), (min(w - 1, fx + int(fw * 1.4)), fy + int(fh * 0.15)), 255, -1)
    
    # Cloth below neck
    cloth_mask = np.zeros((h, w), dtype=np.uint8)
    cloth_top = min(h - 1, chin_y + int(fh * 0.15))
    cv2.rectangle(cloth_mask, (0, cloth_top), (w - 1, h - 1), 255, -1)

    return {
        "skin": full_skin,
        "facial_skin": skin_mask,
        "hair": hair_mask,
        "eyes": eyes_mask,
        "brows": brows_mask,
        "lips": lips_mask,
        "neck": neck_mask,
        "hat": hat_mask,
        "cloth": cloth_mask
    }
