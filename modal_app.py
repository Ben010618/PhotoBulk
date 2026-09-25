"""
KameraPh: Production Serverless Cloud GPU Deployment Script (Modal.com)
------------------------------------------------------------------------
This script deploys the KameraPh AI pipeline onto serverless Nvidia A10G/L4 GPUs.
Imports the unified pipeline module (pipeline.py) to eliminate duplicate logic.
"""

import os
import io
import time
import base64
import numpy as np
from PIL import Image

try:
    import modal
except ImportError:
    modal = None

if modal is not None:
    app = modal.App("kamera-ph-engine")

    # Define container image with GPU acceleration
    kamera_image = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("libgl1-mesa-glx", "libglib2.0-0", "curl")
        .pip_install(
            "opencv-python-headless==4.10.0.84",
            "torch==2.3.1",
            "torchvision==0.18.1",
            "numpy==1.26.4",
            "pillow==10.3.0",
            "rembg==2.0.57",
            "onnxruntime-gpu==1.18.0",
            "fastapi==0.111.0",
            "pydantic==2.7.4"
        )
        .run_commands(
            "mkdir -p /models",
            "curl -L -o /models/face_detection_yunet.onnx https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
            "python -c 'import rembg; rembg.new_session(\"u2net\")'"
        )
    )

    @app.cls(image=kamera_image, gpu="A10G", container_idle_timeout=180)
    class KameraEngine:
        @modal.enter()
        def setup(self):
            import cv2
            import rembg
            print("Warming up GPU and loading neural sessions...")
            self.rembg_session = rembg.new_session("u2net")
            self.yunet_path = "/models/face_detection_yunet.onnx"
            print("KameraEngine ready on Nvidia A10G!")

        @modal.method()
        def process_image(
            self,
            image_bytes: bytes,
            iron_strength: float = 0.70,
            skin_ratio: float = 0.65,
            shine_cut: float = 0.35,
            regalia_profile: str = "standard_toga",
            beauty_preset: str = "morena_radiant"
        ) -> dict:
            import cv2
            from pipeline import process_complete_workflow, crop_8r_aspect, crop_2x2_id

            start_t = time.time()
            nparr = np.frombuffer(image_bytes, np.uint8)
            img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            enhanced_bgr, latency_ms, face_info, engine_label = process_complete_workflow(
                img_bgr,
                bg_replacement_enabled=True,
                backdrop_type="royal_navy",
                beauty_preset=beauty_preset,
                regalia_profile=regalia_profile,
                skin_smoothing=skin_ratio,
                shine_reduction=shine_cut,
                iron_strength=iron_strength
            )

            crop_8r = crop_8r_aspect(enhanced_bgr)
            crop_2x2 = crop_2x2_id(enhanced_bgr, face_info)

            _, enh_buf = cv2.imencode('.jpg', enhanced_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            _, r8_buf = cv2.imencode('.jpg', crop_8r, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            _, id_buf = cv2.imencode('.jpg', crop_2x2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

            return {
                "success": True,
                "latency_ms": latency_ms,
                "engine": "Nvidia A10G (Modal Fleet)",
                "enhanced_bytes": enh_buf.tobytes(),
                "crop_8r_bytes": r8_buf.tobytes(),
                "crop_2x2_bytes": id_buf.tobytes()
            }
