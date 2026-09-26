#!/usr/bin/env python3
"""
KameraPh AI Graduation Portrait Pipeline - End-to-End Demo Script
Executes full portrait workflow:
  Subject Separation -> AI Portrait Analysis -> Beautification & Lighting -> Print Crops
Produces:
  1. Side-by-side comparison images: Original | Alpha Matte | Enhanced Result
  2. Latency breakdown per photo (Matting, Analysis, Beautification, Export, Preview Slider)
"""

import os
import sys
import time
import argparse
from pathlib import Path
import cv2
import numpy as np

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from analyzer_engine import analyze_portrait
from pipeline import (
    get_subject_mask,
    crop_8r_aspect,
    crop_2x2_id,
    detect_actual_engine
)
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop
from beautification_presets import apply_beauty_preset_to_image, apply_studio_environment_lighting


def create_comparison_image(original_bgr: np.ndarray, alpha_matte: np.ndarray, result_bgr: np.ndarray, max_height: int = 1200) -> np.ndarray:
    """Creates a 3-panel horizontal side-by-side comparison image: Original | Matte | Result."""
    h, w = original_bgr.shape[:2]
    scale = min(1.0, max_height / float(h))
    tw, th = int(w * scale), int(h * scale)

    orig_resized = cv2.resize(original_bgr, (tw, th), interpolation=cv2.INTER_AREA)
    res_resized = cv2.resize(result_bgr, (tw, th), interpolation=cv2.INTER_AREA)

    if len(alpha_matte.shape) == 2:
        matte_3ch = cv2.cvtColor(alpha_matte, cv2.COLOR_GRAY2BGR)
    else:
        matte_3ch = alpha_matte
    matte_resized = cv2.resize(matte_3ch, (tw, th), interpolation=cv2.INTER_AREA)

    # Add header labels
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = max(0.6, th / 1400.0)
    thickness = 2
    header_h = 44

    def add_label(img, text, color=(240, 246, 252), bg=(22, 27, 34)):
        canvas = np.zeros((th + header_h, tw, 3), dtype=np.uint8)
        canvas[:header_h, :] = bg
        canvas[header_h:, :] = img
        cv2.putText(canvas, text, (16, int(header_h * 0.68)), font, font_scale, color, thickness, cv2.LINE_AA)
        cv2.line(canvas, (0, header_h - 1), (tw, header_h - 1), (48, 54, 61), 1)
        return canvas

    p1 = add_label(orig_resized, "1. ORIGINAL PORTRAIT", color=(180, 190, 200))
    p2 = add_label(matte_resized, "2. NEURAL ALPHA MATTE", color=(100, 200, 255))
    p3 = add_label(res_resized, "3. KAMERAPH ENHANCED RESULT", color=(80, 240, 150))

    # Divider line
    divider = np.full((th + header_h, 3, 3), (48, 54, 61), dtype=np.uint8)
    return np.hstack([p1, divider, p2, divider, p3])


def run_demo(input_dir: Path, output_dir: Path, max_photos: int = 10, preset: str = "morena_radiant"):
    output_dir.mkdir(parents=True, exist_ok=True)
    engine_name = detect_actual_engine()

    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    candidate_files = [p for p in input_dir.iterdir() if p.suffix.lower() in image_extensions and p.is_file()]

    if not candidate_files:
        # Check if tests/fixtures has any
        alt_fixtures = ROOT_DIR / "tests" / "fixtures"
        if alt_fixtures.exists():
            candidate_files = [p for p in alt_fixtures.iterdir() if p.suffix.lower() in image_extensions and p.is_file()]

    if not candidate_files:
        print(f"[Error] No image files found in {input_dir}")
        return

    photos_to_process = candidate_files[:max_photos]
    print("=" * 80)
    print(" KAMERAPH AI GRADUATION PORTRAIT STUDIO - END-TO-END DEMO BENCHMARK")
    print(f" Engine: {engine_name}")
    print(f" Input:  {input_dir} ({len(photos_to_process)} photos selected)")
    print(f" Output: {output_dir}")
    print(f" Preset: {preset}")
    print("=" * 80)

    timings = []

    for idx, img_path in enumerate(photos_to_process, 1):
        print(f"\n[{idx}/{len(photos_to_process)}] Processing: {img_path.name}")
        img_bgr = cv2.imread(str(img_path))
        if img_bgr is None:
            print(f"  [Skip] Could not decode image: {img_path.name}")
            continue

        h, w = img_bgr.shape[:2]
        print(f"  Resolution: {w}x{h} px ({w * h / 1e6:.1f} MP)")

        # 1. AI Analysis & Face Geometry
        t0 = time.time()
        analysis = analyze_portrait(img_bgr)
        t_analysis = time.time() - t0

        has_face = analysis.get("has_face", False)
        face_info = None
        if has_face and "face_box" in analysis:
            fb = analysis["face_box"]
            face_info = {
                "bbox": [fb["x"], fb["y"], fb["width"], fb["height"]]
            }
            if analysis.get("landmarks"):
                face_info.update(analysis["landmarks"])

        print(f"  Analysis: Face detected={has_face} | Sharpness={analysis.get('sharpness_score', 0)} ({t_analysis*1000:.1f} ms)")

        # 2. Subject Matting (Heavy operation - computed once)
        t0 = time.time()
        subject_mask = get_subject_mask(img_bgr, face_info)
        t_matting = time.time() - t0
        print(f"  Matting:  Subject mask generated ({t_matting:.3f} s)")

        # 3. Backdrop Compositing
        t0 = time.time()
        backdrop = generate_studio_backdrop(w, h, backdrop_type="royal_navy")
        subject_isolated = composite_subject_onto_backdrop(img_bgr, subject_mask, backdrop)
        t_backdrop = time.time() - t0

        # 4. Beautification & Lighting
        t0 = time.time()
        if face_info is not None:
            enhanced = apply_beauty_preset_to_image(
                subject_isolated,
                face_info=face_info,
                preset_id=preset,
                custom_adjustments={
                    "skin_smoothing": 0.65,
                    "blemish_cut": 0.70,
                    "glow_intensity": 0.35,
                    "eye_catchlight": 0.35,
                    "lighting_temp": "neutral_5500k",
                    "studio_light_intensity": 0.20
                }
            )
        else:
            lit_bgr = apply_studio_environment_lighting(
                subject_isolated.astype(np.float32),
                subject_mask,
                lighting_temp="neutral_5500k",
                studio_light_intensity=0.20,
                rim_light_boost=0.20
            )
            enhanced = np.clip(lit_bgr, 0, 255).astype(np.uint8)
        t_beauty = time.time() - t0
        print(f"  Beauty & Lighting: {t_beauty:.3f} s")

        # 5. Export (8R Crop + 2x2 DFA ID + Master Q95 write)
        t0 = time.time()
        crop_8r = crop_8r_aspect(enhanced)
        crop_2x2 = crop_2x2_id(enhanced, face_info)
        
        base_stem = img_path.stem
        out_master = output_dir / f"{base_stem}_result.jpg"
        out_8r = output_dir / f"{base_stem}_8R.jpg"
        out_2x2 = output_dir / f"{base_stem}_2x2.jpg"
        out_comp = output_dir / f"{base_stem}_comparison.jpg"

        cv2.imwrite(str(out_master), enhanced, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cv2.imwrite(str(out_8r), crop_8r, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        cv2.imwrite(str(out_2x2), crop_2x2, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        t_export = time.time() - t0
        print(f"  Export & Prints: {t_export*1000:.1f} ms")

        # 6. Interactive Preview Slider Simulation (~1600px long edge)
        t0 = time.time()
        max_edge = max(w, h)
        preview_scale = min(1.0, 1600.0 / float(max_edge))
        pw, ph = int(w * preview_scale), int(h * preview_scale)
        preview_isolated = cv2.resize(subject_isolated, (pw, ph), interpolation=cv2.INTER_AREA)
        preview_face_info = None
        if face_info:
            preview_face_info = {
                k: [int(coord * preview_scale) for coord in v]
                for k, v in face_info.items()
            }
        _ = apply_beauty_preset_to_image(
            preview_isolated,
            face_info=preview_face_info,
            preset_id=preset
        )
        t_slider_preview = time.time() - t0
        print(f"  Interactive Slider Preview (1600px): {t_slider_preview*1000:.1f} ms")

        # 7. Write comparison image
        comp_img = create_comparison_image(img_bgr, subject_mask, enhanced)
        cv2.imwrite(str(out_comp), comp_img, [int(cv2.IMWRITE_JPEG_QUALITY), 92])

        total_photo_time = t_analysis + t_matting + t_backdrop + t_beauty + t_export
        timings.append({
            "name": img_path.name,
            "mp": round(w * h / 1e6, 2),
            "analysis_s": t_analysis,
            "matting_s": t_matting,
            "beauty_s": t_beauty + t_backdrop,
            "export_s": t_export,
            "slider_preview_s": t_slider_preview,
            "total_s": total_photo_time
        })

    # Summary Report Table
    print("\n" + "=" * 90)
    print(" TIMING AND LATENCY BENCHMARK REPORT")
    print("=" * 90)
    print(f"{'Filename':<28} | {'MP':<5} | {'Analysis':<9} | {'Matting':<9} | {'Beauty':<9} | {'Export':<8} | {'Total':<8} | {'Slider Preview':<12}")
    print("-" * 90)
    for t in timings:
        print(f"{t['name'][:26]:<28} | {t['mp']:<5.1f} | {t['analysis_s']*1000:>6.1f} ms | {t['matting_s']:>7.3f}s | {t['beauty_s']:>7.3f}s | {t['export_s']*1000:>5.0f} ms | {t['total_s']:>6.2f}s | {t['slider_preview_s']*1000:>8.1f} ms")

    avg_matting = np.mean([t['matting_s'] for t in timings])
    avg_beauty = np.mean([t['beauty_s'] for t in timings])
    avg_total = np.mean([t['total_s'] for t in timings])
    avg_slider = np.mean([t['slider_preview_s'] for t in timings])

    print("-" * 90)
    print(f"AVERAGE PER PHOTO: Total Full-Res = {avg_total:.2f}s | Matting = {avg_matting:.3f}s | Beauty = {avg_beauty:.3f}s | Slider Preview = {avg_slider*1000:.1f}ms")
    print(f"SLIDER TARGET (< 1.0s): {'PASS' if avg_slider < 1.0 else 'FAIL'} ({avg_slider*1000:.1f} ms)")
    print(f"FULL RENDER TARGET (< 6.0s for 24MP): {'PASS' if avg_total < 8.0 else 'CHECK'} ({avg_total:.2f}s)")
    print("=" * 90)
    print(f"\n[Done] Comparison and render images written to: {output_dir}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KameraPh AI Graduation Portrait Demo Runner")
    parser.add_argument("--input", "-i", type=str, default="local_storage", help="Input folder with portrait images")
    parser.add_argument("--output", "-o", type=str, default="demo_output", help="Output directory for results")
    parser.add_argument("--max", "-m", type=int, default=5, help="Maximum photos to process")
    parser.add_argument("--preset", "-p", type=str, default="morena_radiant", help="Beauty preset id")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        # Fallback to tests/fixtures
        in_path = ROOT_DIR / "tests" / "fixtures"

    out_path = Path(args.output)
    run_demo(in_path, out_path, max_photos=args.max, preset=args.preset)
