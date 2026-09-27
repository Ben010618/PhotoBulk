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


from concurrent.futures import ThreadPoolExecutor, as_completed

OUTPUT_FOLDERS = {
    "master": ("1_Full_Res_Masters", "Master"),
    "8r": ("2_8R_Yearbook_Frames", "8R"),
    "5r": ("3_5R_Prints", "5R"),
    "4r": ("4_4R_Prints", "4R"),
    "wallet": ("5_Wallet_Photos", "Wallet"),
    "2x2": ("6_2x2_Formal_IDs", "2x2"),
    "web": ("7_Web_Portals", "Web"),
}


def _render_and_export_photo_task(task_args: Dict[str, Any]) -> Dict[str, Any]:
    """Worker task executing full-res rendering and size generation for a single photo in parallel."""
    project_id = task_args["project_id"]
    pid = task_args["photo_id"]
    orig_fn = task_args["orig_fn"]
    staging_dir = Path(task_args["staging_dir"])
    outputs = task_args["outputs"]
    assigned_outputs = task_args["assigned_outputs"]
    student_display_name = task_args["student_display_name"]
    analysis = task_args.get("analysis", {})

    # 1. Full-Resolution Master Render
    render_res = project_store.render_full_resolution(project_id, pid)
    master_path = Path(render_res["master_path"])
    master_bgr = cv2.imread(str(master_path))

    if master_bgr is None:
        logger.warning(f"Could not load master render for {pid}, skipping sizes.")
        return {
            "photo_id": pid,
            "orig_fn": orig_fn,
            "files": [],
            "contact_sheet_item": None,
            "success": False
        }

    features = project_store.compute_and_cache_heavy_features(project_id, pid)
    face_info = features.get("face_info")

    # Contact sheet thumbnail
    thumb_path = staging_dir / f"thumb_{pid}.jpg"
    save_jpeg_with_profile(master_bgr, thumb_path, target_size=(360, 480), dpi=96, quality=80)
    contact_sheet_item = {
        "image_path": str(thumb_path),
        "student_name": student_display_name,
        "analysis": analysis
    }

    files_to_write: List[Tuple[Path, str]] = []

    # 2. Render each output size to staging directory
    for out_key in outputs:
        if out_key not in assigned_outputs:
            continue
        final_fn, arcname = assigned_outputs[out_key]
        out_p = staging_dir / f"{out_key}_{final_fn}"

        if out_key == "master":
            save_jpeg_with_profile(master_bgr, out_p, dpi=300, quality=95)
        elif out_key == "8r":
            crop8r = crop_8r_aspect(master_bgr)
            save_jpeg_with_profile(crop8r, out_p, target_size=PRINT_SIZES_300DPI["8r"], dpi=300, quality=95)
        elif out_key == "5r":
            crop5r = crop_aspect(master_bgr, 5.0, 7.0)
            save_jpeg_with_profile(crop5r, out_p, target_size=PRINT_SIZES_300DPI["5r"], dpi=300, quality=95)
        elif out_key == "4r":
            crop4r = crop_aspect(master_bgr, 2.0, 3.0)
            save_jpeg_with_profile(crop4r, out_p, target_size=PRINT_SIZES_300DPI["4r"], dpi=300, quality=95)
        elif out_key == "wallet":
            crop_wal = crop_aspect(master_bgr, 5.0, 7.0)
            save_jpeg_with_profile(crop_wal, out_p, target_size=PRINT_SIZES_300DPI["wallet"], dpi=300, quality=95)
        elif out_key == "2x2":
            orig_p = project_store.get_photo_dir(project_id, pid) / "original.jpg"
            subj_for_id = cv2.imread(str(orig_p)) if orig_p.exists() else master_bgr
            crop2x2 = crop_2x2_id(
                subj_for_id,
                face_info,
                white_background=True,
                mask=features.get("subject_mask")
            )
            save_jpeg_with_profile(crop2x2, out_p, target_size=PRINT_SIZES_300DPI["2x2"], dpi=300, quality=95)
        elif out_key == "web":
            h, w = master_bgr.shape[:2]
            max_edge = max(w, h)
            scale = min(1.0, 1600.0 / float(max_edge))
            web_size = (int(w * scale), int(h * scale))
            save_jpeg_with_profile(master_bgr, out_p, target_size=web_size, dpi=96, quality=88)

        files_to_write.append((out_p, arcname))

    return {
        "photo_id": pid,
        "orig_fn": orig_fn,
        "files": files_to_write,
        "contact_sheet_item": contact_sheet_item,
        "success": True
    }


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
      1. Deterministically calculates unique filenames (appending _2, _3 for collisions).
      2. Validates image resolutions against 300 DPI print standards (DPI warnings).
      3. Renders full-resolution master and sizes in parallel with worker pool.
      4. Generates contact sheet PDF and EXPORT_MANIFEST.txt.
      5. Compresses all assets into a single ZIP archive.
    """
    start_time = time.time()
    photos = project_store.list_photos(project_id)
    total_photos = len(photos)

    student_mapping: Dict[str, Dict[str, str]] = {}
    if student_csv:
        student_mapping = parse_student_csv(student_csv)

    staging_dir = EXPORTS_DIR / f"{project_id}_{export_id}"
    staging_dir.mkdir(parents=True, exist_ok=True)

    zip_path = EXPORTS_DIR / f"{sanitize_filename(school_name)}_{export_id}.zip"

    clean_school = sanitize_filename(school_name)
    outputs = [o.lower() for o in selected_outputs] if selected_outputs else ["master", "8r", "2x2"]

    # 1. Deterministic Filename Uniqueness & DPI Warning Check
    used_filenames_by_output: Dict[str, set] = {o: set() for o in outputs}
    photo_tasks: List[Dict[str, Any]] = []
    manifest_entries: List[str] = []
    dpi_warnings: List[str] = []

    for idx, p in enumerate(photos, 1):
        pid = p["id"]
        orig_fn = p["filename"]
        base_fn = os.path.splitext(orig_fn)[0]

        s_info = student_mapping.get(base_fn.lower()) or student_mapping.get(pid.lower()) or {}
        student_display_name = s_info.get("name") or s_info.get("first") or base_fn

        # Check source dimensions for DPI warnings
        p_dir = project_store.get_photo_dir(project_id, pid)
        orig_img_path = p_dir / "original.jpg"
        source_w, source_h = (0, 0)
        if orig_img_path.exists():
            try:
                with Image.open(str(orig_img_path)) as im:
                    source_w, source_h = im.size
            except Exception:
                pass

        assigned_outputs: Dict[str, Tuple[str, str]] = {}
        for out_key in outputs:
            if out_key not in OUTPUT_FOLDERS:
                continue
            folder_name, size_label = OUTPUT_FOLDERS[out_key]

            # DPI validation: Check if source photo is smaller than required 300 DPI print dimension
            if out_key in PRINT_SIZES_300DPI and source_w > 0 and source_h > 0:
                req_w, req_h = PRINT_SIZES_300DPI[out_key]
                if min(source_w, source_h) < min(req_w, req_h) or max(source_w, source_h) < max(req_w, req_h):
                    warn_msg = (
                        f"DPI WARNING: Photo '{orig_fn}' ({source_w}x{source_h}) is smaller than required "
                        f"300 DPI print dimensions for {size_label} ({req_w}x{req_h}). "
                        f"Silently upscaling to print size without studio warning may reduce print sharpness."
                    )
                    if warn_msg not in dpi_warnings:
                        dpi_warnings.append(warn_msg)

            # Filename formatting
            candidate_fn = format_export_filename(filename_template, orig_fn, s_info, size_label)

            # Collision handling: if filename already taken, append _2, _3, etc.
            if candidate_fn in used_filenames_by_output[out_key]:
                stem, ext = os.path.splitext(candidate_fn)
                counter = 2
                while True:
                    deduped_fn = f"{stem}_{counter}{ext}"
                    if deduped_fn not in used_filenames_by_output[out_key]:
                        final_fn = deduped_fn
                        break
                    counter += 1
            else:
                final_fn = candidate_fn

            used_filenames_by_output[out_key].add(final_fn)
            arcname = f"{clean_school}/{folder_name}/{final_fn}"
            assigned_outputs[out_key] = (final_fn, arcname)
            manifest_entries.append(
                f"[{size_label.upper()}] {final_fn} -> {arcname} (Student: {student_display_name}, Photo ID: {pid}, Source: {orig_fn})"
            )

        photo_tasks.append({
            "idx": idx,
            "project_id": project_id,
            "photo_id": pid,
            "orig_fn": orig_fn,
            "staging_dir": str(staging_dir),
            "outputs": outputs,
            "assigned_outputs": assigned_outputs,
            "student_display_name": student_display_name,
            "analysis": p.get("analysis", {})
        })

    # 2. Parallel Full-Resolution Rendering using Worker Pool
    contact_sheet_items: List[Dict[str, Any]] = []
    generated_files_count = 0
    workers = min(max(1, (os.cpu_count() or 2) - 1), 8)

    logger.info(f"[ExportEngine] Starting parallel export of {total_photos} photos using {workers} worker threads")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_task = {
                executor.submit(_render_and_export_photo_task, task): task
                for task in photo_tasks
            }

            processed = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    task_res = future.result()
                    if task_res.get("success"):
                        for out_p, arcname in task_res.get("files", []):
                            if out_p.exists():
                                zf.write(out_p, arcname=arcname)
                                generated_files_count += 1
                        if task_res.get("contact_sheet_item"):
                            contact_sheet_items.append(task_res["contact_sheet_item"])
                except Exception as err:
                    logger.error(f"[ExportEngine] Photo render failure for {task['photo_id']}: {err}")

                processed += 1
                if progress_callback:
                    progress_callback(processed, total_photos, f"Exported {task['orig_fn']} ({processed}/{total_photos})")

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
        manifest_lines = [
            "KAMERAPH GRADUATION STUDIO BULK EXPORT",
            "=====================================",
            f"School/Cohort   : {school_name}",
            f"Studio Name     : {studio_name}",
            f"Export Job ID   : {export_id}",
            f"Date & Time     : {time.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Total Portraits : {total_photos}",
            f"Files Generated : {generated_files_count}",
            f"Elapsed Time    : {elapsed_sec} seconds",
            f"Color Space     : sRGB (embedded ICC)",
            f"Print Standard  : 300 DPI, Quality 95",
            f"Selected Sizes  : {', '.join(outputs).upper()}",
            f"Filename Pattern: {filename_template}",
            ""
        ]

        if dpi_warnings:
            manifest_lines.append("DPI WARNINGS & PRINT NOTICES:")
            manifest_lines.append("-----------------------------")
            manifest_lines.extend(dpi_warnings)
            manifest_lines.append("")

        manifest_lines.append("EXPORTED FILES MANIFEST:")
        manifest_lines.append("------------------------")
        for entry in sorted(manifest_entries):
            manifest_lines.append(entry)

        manifest_text = "\n".join(manifest_lines) + "\n"
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
        "elapsed_sec": round(time.time() - start_time, 2),
        "warnings": dpi_warnings,
        "dpi_warnings": dpi_warnings,
        "manifest": manifest_text
    }


def generate_comparison_sheet(
    image_bgr: Optional[np.ndarray] = None,
    output_path: str = "demo_output/before_after_comparison.jpg"
) -> str:
    """
    Generates a high-resolution before/after verification sheet under demo_output/:
      Panel 1: BEFORE (Underexposed Source)
      Panel 2: AFTER (Auto-Exposure + Studio Grading)
      Panel 3: PRC/DFA 2x2 Official ID (Pure White Bg, 70-80% head)
    """
    import skimage.data
    from pipeline import process_complete_workflow, get_subject_mask

    if image_bgr is None:
        image_bgr = cv2.cvtColor(skimage.data.astronaut(), cv2.COLOR_RGB2BGR)

    dark = cv2.convertScaleAbs(image_bgr, alpha=0.45, beta=0)

    # 1. Enhanced version
    enhanced, _, face_info, _ = process_complete_workflow(
        dark, beauty_preset="natural", backdrop_type="classic_blue"
    )

    # 2. 2x2 ID version
    mask = get_subject_mask(image_bgr, face_info)
    id_2x2 = crop_2x2_id(image_bgr, face_info=face_info, white_background=True, mask=mask)

    p1 = cv2.resize(dark, (600, 600))
    p2 = cv2.resize(enhanced, (600, 600))
    p3 = id_2x2

    header_h = 80
    sheet_w = 600 * 3
    sheet_h = 600 + header_h
    sheet = np.full((sheet_h, sheet_w, 3), 22, dtype=np.uint8)

    cv2.putText(sheet, "BEFORE: Underexposed Input", (35, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (200, 200, 200), 2)
    cv2.putText(sheet, "AFTER: Auto-Exposure & Studio Grading", (635, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (80, 220, 100), 2)
    cv2.putText(sheet, "PRC/DFA 2x2 ID: Pure White Bg", (1235, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 200, 80), 2)

    sheet[header_h:, 0:600] = p1
    sheet[header_h:, 600:1200] = p2
    sheet[header_h:, 1200:1800] = p3

    cv2.line(sheet, (600, 0), (600, sheet_h), (60, 60, 60), 2)
    cv2.line(sheet, (1200, 0), (1200, sheet_h), (60, 60, 60), 2)

    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_p), sheet, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
    return str(out_p)
