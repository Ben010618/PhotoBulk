"""
KameraPh Studio Watermarking & Mobile Proofing Verification Engine
------------------------------------------------------------------
Embeds semi-transparent security watermarks, student identification footers,
and dynamic QR codes linking to the live mobile proofing verification portal.
"""

import os
import cv2
import numpy as np
import qrcode
from PIL import Image
from typing import Optional

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
