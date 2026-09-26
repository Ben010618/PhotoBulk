"""
KameraPh Bulk Export Engine
---------------------------
High-performance batch export processor for school graduation portraiture:
  - Supports multiple outputs: Master, 8R (8x10), 5R (5x7), 4R (4x6), Wallet (2.5x3.5), 2x2 ID, Web JPEG.
  - Correct 300 DPI and sRGB ICC profile embedded into every JPEG (Quality 95).
  - Filename templating (e.g. {section}_{last}_{first}_{size}.jpg) with CSV student name mapping.
  - Multi-up proofing Contact Sheet PDF included in archive.
  - Packages results into a single structured ZIP file for secure studio download.
"""

import os
import io
import re
import csv
import time
import zipfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
import cv2
import numpy as np
from PIL import Image, ImageCms

from config import DATA_DIR
from project_store import project_store
from pipeline import crop_8r_aspect, crop_2x2_id
from pdf_engine import generate_contact_sheet_pdf

logger = logging.getLogger("kameraph.export_engine")

EXPORTS_DIR = Path(DATA_DIR) / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Standard print dimensions at 300 DPI (width, height in pixels)
PRINT_SIZES_300DPI = {
    "8r": (2400, 3000),      # 8x10 inches (4:5)
    "5r": (1500, 2100),      # 5x7 inches (5:7)
    "4r": (1200, 1800),      # 4x6 inches (2:3)
    "wallet": (750, 1050),   # 2.5x3.5 inches (5:7)
    "2x2": (600, 600),       # 2x2 inches (1:1)
}

# Cached sRGB ICC profile bytes
_SRGB_PROFILE_BYTES: Optional[bytes] = None


def get_srgb_profile_bytes() -> bytes:
    """Generates standard sRGB color profile bytes via PIL ImageCms."""
    global _SRGB_PROFILE_BYTES
    if _SRGB_PROFILE_BYTES is None:
        try:
            profile = ImageCms.createProfile("sRGB")
            _SRGB_PROFILE_BYTES = ImageCms.ImageCmsProfile(profile).tobytes()
        except Exception as e:
            logger.warning(f"Failed to generate sRGB profile via ImageCms: {e}")
            _SRGB_PROFILE_BYTES = b""
    return _SRGB_PROFILE_BYTES


def sanitize_filename(name: str) -> str:
    """Strips path traversal and invalid characters from filename component."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name)
    cleaned = re.sub(r'\s+', '_', cleaned)
    return cleaned.strip()


def crop_aspect(img_bgr: np.ndarray, target_w_ratio: float, target_h_ratio: float) -> np.ndarray:
    """Crops portrait to arbitrary aspect ratio, centering horizontally and framing vertically."""
    h, w = img_bgr.shape[:2]
    target_aspect = float(target_w_ratio) / float(target_h_ratio)
    current_aspect = float(w) / float(h)

    if current_aspect > target_aspect:
        new_w = int(h * target_aspect)
        start_x = (w - new_w) // 2
        return img_bgr[:, start_x:start_x + new_w]
    else:
        new_h = int(w / target_aspect)
        start_y = max(0, int((h - new_h) * 0.20))
        return img_bgr[start_y:start_y + new_h, :]


def save_jpeg_with_profile(
    img_bgr: np.ndarray,
    dest_path: Path,
    target_size: Optional[Tuple[int, int]] = None,
    dpi: int = 300,
    quality: int = 95
):
    """
    Saves image as JPEG with explicit 300 DPI and embedded standard sRGB ICC profile.
    """
    if target_size:
        tw, th = target_size
        img_bgr = cv2.resize(img_bgr, (tw, th), interpolation=cv2.INTER_LANCZOS4)

    # Convert BGR to RGB for Pillow
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb)

    srgb_bytes = get_srgb_profile_bytes()
    save_kwargs: Dict[str, Any] = {
        "format": "JPEG",
        "dpi": (dpi, dpi),
        "quality": quality,
        "subsampling": 0
    }
    if srgb_bytes:
        save_kwargs["icc_profile"] = srgb_bytes

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    pil_img.save(str(dest_path), **save_kwargs)


def parse_student_csv(csv_content: str) -> Dict[str, Dict[str, str]]:
    """
    Parses CSV content into mapping:
    key (lowercase filename without extension or student_id) -> {first, last, section, student_id, name}
    """
    mapping: Dict[str, Dict[str, str]] = {}
    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        # Standardize field names
        clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k and v}
        first = clean_row.get("first_name") or clean_row.get("first") or clean_row.get("firstname") or ""
        last = clean_row.get("last_name") or clean_row.get("last") or clean_row.get("lastname") or ""
        section = clean_row.get("section") or clean_row.get("class") or clean_row.get("cohort") or "Graduation"
        student_id = clean_row.get("student_id") or clean_row.get("id") or clean_row.get("lrn") or ""
        name = clean_row.get("name") or clean_row.get("student_name") or f"{first} {last}".strip()

        fn_key = clean_row.get("filename") or clean_row.get("file") or ""
        info = {
            "first": first,
            "last": last,
            "section": section,
            "student_id": student_id,
            "name": name
        }

        if fn_key:
            base_key = os.path.splitext(fn_key)[0].strip().lower()
            mapping[base_key] = info
        if student_id:
            mapping[student_id.strip().lower()] = info

    return mapping


def format_export_filename(
    template: str,
    original_filename: str,
    student_info: Dict[str, str],
    size_label: str
) -> str:
    """
    Formats filename using template such as:
      {section}_{last}_{first}_{size}.jpg
    """
    base_fn = os.path.splitext(original_filename)[0]
    first = student_info.get("first") or base_fn
    last = student_info.get("last") or ""
    section = student_info.get("section") or "Graduation"
    student_id = student_info.get("student_id") or ""
    full_name = student_info.get("name") or f"{first}_{last}".strip("_")

    formatted = template
    formatted = formatted.replace("{section}", sanitize_filename(section))
    formatted = formatted.replace("{last}", sanitize_filename(last))
    formatted = formatted.replace("{first}", sanitize_filename(first))
    formatted = formatted.replace("{student_id}", sanitize_filename(student_id))
    formatted = formatted.replace("{name}", sanitize_filename(full_name))
    formatted = formatted.replace("{filename}", sanitize_filename(base_fn))
    formatted = formatted.replace("{size}", sanitize_filename(size_label))

    # Clean double underscores
    cleaned = re.sub(r'_+', '_', formatted).strip('_')
    if not cleaned.lower().endswith(".jpg"):
        cleaned += ".jpg"
    return cleaned


def execute_bulk_export(
    project_id: str,
    export_id: str,
    selected_outputs: List[str],
    filename_template: str = "{section}_{last}_{first}_{size}.jpg",
    student_csv: Optional[str] = None,
    school_name: str = "Graduation Batch 2026",
    studio_name: str = "AuraGrad Creative Studio",
    include_contact_sheet: bool = True,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> Dict[str, Any]:
    """
    Executes full-resolution bulk export:
      1. Renders full-resolution master for each photo.
      2. Generates selected sizes at 300 DPI with sRGB profile embedded.
      3. Generates contact sheet PDF.
      4. Compresses all assets into a single ZIP archive.
    """
    start_time = time.time()
    photos = project_store.list_photos(project_id)
    total_photos = len(photos)

    student_mapping: Dict[str, Dict[str, str]] = {}
    if student_csv:
        student_mapping = parse_student_csv(student_csv)

    # Output directory for staged export files
    staging_dir = EXPORTS_DIR / f"{project_id}_{export_id}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    zip_path = EXPORTS_DIR / f"{sanitize_filename(school_name)}_{export_id}.zip"

    contact_sheet_items: List[Dict[str, Any]] = []
    generated_files_count = 0

    clean_school = sanitize_filename(school_name)
    outputs = [o.lower() for o in selected_outputs] if selected_outputs else ["master", "8r", "2x2"]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, p in enumerate(photos, 1):
            pid = p["id"]
            orig_fn = p["filename"]
            base_fn = os.path.splitext(orig_fn)[0]

            # Find student info from mapping
            s_info = student_mapping.get(base_fn.lower()) or student_mapping.get(pid.lower()) or {}
            student_display_name = s_info.get("name") or s_info.get("first") or base_fn

            if progress_callback:
                progress_callback(idx, total_photos, f"Rendering {orig_fn} ({idx}/{total_photos})")

            # 1. Full-Resolution Master Render
            render_res = project_store.render_full_resolution(project_id, pid)
            master_path = Path(render_res["master_path"])
            master_bgr = cv2.imread(str(master_path))

            if master_bgr is None:
                logger.warning(f"Could not load master render for {pid}, skipping sizes.")
                continue

            features = project_store.compute_and_cache_heavy_features(project_id, pid)
            face_info = features.get("face_info")

            # Contact sheet thumbnail collection
            thumb_path = staging_dir / f"thumb_{pid}.jpg"
            save_jpeg_with_profile(master_bgr, thumb_path, target_size=(360, 480), dpi=96, quality=80)
            contact_sheet_items.append({
                "image_path": str(thumb_path),
                "student_name": student_display_name,
                "analysis": p.get("analysis", {})
            })

            # 2. Generate and write selected outputs
            # Master
            if "master" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "Master")
                out_p = staging_dir / f"master_{fn}"
                save_jpeg_with_profile(master_bgr, out_p, dpi=300, quality=95)
                zf.write(out_p, arcname=f"{clean_school}/1_Full_Res_Masters/{fn}")
                generated_files_count += 1

            # 8R (8x10 inches at 300 DPI -> 2400x3000)
            if "8r" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "8R")
                crop8r = crop_8r_aspect(master_bgr)
                out_p = staging_dir / f"8r_{fn}"
                save_jpeg_with_profile(crop8r, out_p, target_size=PRINT_SIZES_300DPI["8r"], dpi=300, quality=95)
                zf.write(out_p, arcname=f"{clean_school}/2_8R_Yearbook_Frames/{fn}")
                generated_files_count += 1

            # 5R (5x7 inches at 300 DPI -> 1500x2100)
            if "5r" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "5R")
                crop5r = crop_aspect(master_bgr, 5.0, 7.0)
                out_p = staging_dir / f"5r_{fn}"
                save_jpeg_with_profile(crop5r, out_p, target_size=PRINT_SIZES_300DPI["5r"], dpi=300, quality=95)
                zf.write(out_p, arcname=f"{clean_school}/3_5R_Prints/{fn}")
                generated_files_count += 1

            # 4R (4x6 inches at 300 DPI -> 1200x1800)
            if "4r" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "4R")
                crop4r = crop_aspect(master_bgr, 2.0, 3.0)
                out_p = staging_dir / f"4r_{fn}"
                save_jpeg_with_profile(crop4r, out_p, target_size=PRINT_SIZES_300DPI["4r"], dpi=300, quality=95)
                zf.write(out_p, arcname=f"{clean_school}/4_4R_Prints/{fn}")
                generated_files_count += 1

            # Wallet (2.5x3.5 inches at 300 DPI -> 750x1050)
            if "wallet" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "Wallet")
                crop_wal = crop_aspect(master_bgr, 5.0, 7.0)
                out_p = staging_dir / f"wallet_{fn}"
                save_jpeg_with_profile(crop_wal, out_p, target_size=PRINT_SIZES_300DPI["wallet"], dpi=300, quality=95)
                zf.write(out_p, arcname=f"{clean_school}/5_Wallet_Photos/{fn}")
                generated_files_count += 1

            # 2x2 Formal ID (600x600 px at 300 DPI)
            if "2x2" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "2x2")
                crop2x2 = crop_2x2_id(master_bgr, face_info)
                out_p = staging_dir / f"2x2_{fn}"
                save_jpeg_with_profile(crop2x2, out_p, target_size=PRINT_SIZES_300DPI["2x2"], dpi=300, quality=95)
                zf.write(out_p, arcname=f"{clean_school}/6_2x2_Formal_IDs/{fn}")
                generated_files_count += 1

            # Web JPEG (max 1600px long edge, ~96 DPI, Quality 88)
            if "web" in outputs:
                fn = format_export_filename(filename_template, orig_fn, s_info, "Web")
                h, w = master_bgr.shape[:2]
                max_edge = max(w, h)
                scale = min(1.0, 1600.0 / float(max_edge))
                web_size = (int(w * scale), int(h * scale))
                out_p = staging_dir / f"web_{fn}"
                save_jpeg_with_profile(master_bgr, out_p, target_size=web_size, dpi=96, quality=88)
                zf.write(out_p, arcname=f"{clean_school}/7_Web_Portals/{fn}")
                generated_files_count += 1

        # 3. Add Contact Sheet PDF
        if include_contact_sheet and contact_sheet_items:
            if progress_callback:
                progress_callback(total_photos, total_photos, "Generating Contact Sheet PDF...")
            try:
                pdf_bytes = generate_contact_sheet_pdf(
                    contact_sheet_items,
                    studio_name=studio_name,
                    school_name=school_name
                )
                zf.writestr(f"{clean_school}/Contact_Sheet_{clean_school}.pdf", pdf_bytes)
            except Exception as e:
                logger.error(f"Failed to generate contact sheet PDF: {e}")

        # 4. Add Manifest Summary TXT
        elapsed_sec = round(time.time() - start_time, 2)
        manifest_text = (
            f"KAMERAPH GRADUATION STUDIO BULK EXPORT\n"
            f"=====================================\n"
            f"School/Cohort   : {school_name}\n"
            f"Studio Name     : {studio_name}\n"
            f"Export Job ID   : {export_id}\n"
            f"Date & Time     : {time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"Total Portraits : {total_photos}\n"
            f"Files Generated : {generated_files_count}\n"
            f"Elapsed Time    : {elapsed_sec} seconds\n"
            f"Color Space     : sRGB (embedded ICC)\n"
            f"Print Standard  : 300 DPI, Quality 95\n"
            f"Selected Sizes  : {', '.join(outputs).upper()}\n"
            f"Filename Pattern: {filename_template}\n"
        )
        zf.writestr(f"{clean_school}/EXPORT_MANIFEST.txt", manifest_text)

    # Clean up staging temporary images
    try:
        import shutil
        shutil.rmtree(staging_dir, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Notice cleaning up staging dir {staging_dir}: {e}")

    file_size_bytes = zip_path.stat().st_size if zip_path.exists() else 0
    return {
        "export_id": export_id,
        "zip_path": str(zip_path),
        "filename": zip_path.name,
        "file_size_bytes": file_size_bytes,
        "total_portraits": total_photos,
        "total_files": generated_files_count,
        "elapsed_sec": round(time.time() - start_time, 2)
    }
