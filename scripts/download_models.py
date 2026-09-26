"""
Model Downloader and Checksum Verifier for KameraPh.
Verifies SHA256 checksums for neural models:
- YuNet Face Detector (face_detection_yunet.onnx)
- BiSeNet Face Parsing (bisenet_face_parsing.onnx)
"""

import os
import sys
import hashlib
from pathlib import Path
import urllib.request

BASE_DIR = Path(__file__).resolve().parent.parent

MODELS = {
    "face_detection_yunet.onnx": {
        "url": "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
        "sha256": "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
        "size_desc": "~336 KB",
        "required": True,
        "fallback_desc": "None (YuNet required for face landmarks)"
    },
    "bisenet_face_parsing.onnx": {
        "url": "https://github.com/yakhyo/face-reidentification/releases/download/v0.1.0/bisenet_face_parsing.onnx",
        "sha256": "0d9bd318e46987c3bdbfacae9e2c0f461cae1c6ac6ea6d43bbe541a91727e33f",
        "size_desc": "~53 MB",
        "required": False,
        "fallback_desc": "Geometric anatomical landmark fallback is automatically active when missing"
    }
}


def compute_sha256(filepath: Path) -> str:
    """Computes SHA256 checksum of a file in 64KB chunks."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def check_and_download_model(name: str, spec: dict) -> bool:
    target_path = BASE_DIR / name
    expected_sha = spec["sha256"]

    if target_path.exists():
        actual_sha = compute_sha256(target_path)
        if actual_sha == expected_sha:
            print(f"[OK] {name} present and verified (SHA256: {actual_sha[:16]}...)")
            return True
        else:
            print(f"[WARN] {name} checksum mismatch! Expected {expected_sha}, got {actual_sha}")
    
    print(f"[*] Downloading {name} ({spec['size_desc']})...")
    try:
        urllib.request.urlretrieve(spec["url"], str(target_path))
        actual_sha = compute_sha256(target_path)
        if actual_sha == expected_sha:
            print(f"[OK] Downloaded and verified {name} successfully.")
            return True
        else:
            print(f"[ERROR] Downloaded {name} has incorrect checksum: {actual_sha}")
            return False
    except Exception as e:
        print(f"[WARN] Could not download {name}: {e}")
        if not spec["required"]:
            print(f"       Note: {spec['fallback_desc']}.")
        return False


def main():
    print("=" * 60)
    print("KameraPh AI Model Checksum Verification & Download")
    print("=" * 60)
    all_ok = True
    for name, spec in MODELS.items():
        ok = check_and_download_model(name, spec)
        if spec["required"] and not ok:
            all_ok = False

    if all_ok:
        print("\nAll required models are present and verified.")
    else:
        print("\nWarning: One or more required models could not be verified.")
        sys.exit(1)


if __name__ == "__main__":
    main()
