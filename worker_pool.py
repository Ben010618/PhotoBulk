"""
KameraPh Worker Pool (Multiprocessing CPU Worker Pool for Bulk Processing)
-------------------------------------------------------------------------
Executes bulk processing across CPU cores using concurrent.futures.ProcessPoolExecutor:
  - 1 process per CPU core (or configured limit).
  - Models (YuNet Face Detector & rembg U2Net session) loaded once per process initializer.
  - Updates progress per photo every 1 to 2 seconds.
"""

import os
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path

logger = logging.getLogger("kameraph.worker_pool")

# Global process-local model instances
_WORKER_YUNET = None
_WORKER_REMBG = None


def init_worker_process():
    """Initializes models once per worker process."""
    global _WORKER_YUNET, _WORKER_REMBG
    try:
        from analyzer_engine import get_face_detector
        _WORKER_YUNET = get_face_detector((640, 640))
    except Exception as e:
        logger.warning(f"[WorkerInit] YuNet init notice: {e}")

    try:
        from pipeline import get_rembg_session
        _WORKER_REMBG = get_rembg_session()
    except Exception as e:
        logger.warning(f"[WorkerInit] rembg init notice: {e}")


def process_single_photo_task(
    project_id: str,
    photo_id: str,
    custom_settings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Worker task: executes heavy feature caching and full-res render for a photo."""
    start_time = time.time()
    from project_store import project_store

    try:
        # 1. Compute & cache heavy features if not already cached
        features = project_store.compute_and_cache_heavy_features(project_id, photo_id)
        face_info = features.get("face_info")
        analysis = features.get("analysis", {})

        # 2. Render preview image
        preview_bgr, preview_lat = project_store.render_preview_fast(
            project_id, photo_id, custom_settings=custom_settings
        )

        total_lat = max(1, int((time.time() - start_time) * 1000))
        return {
            "photo_id": photo_id,
            "project_id": project_id,
            "success": True,
            "has_face": analysis.get("has_face", False),
            "review_needed": analysis.get("review_needed", False),
            "review_reason": analysis.get("review_reason"),
            "latency_ms": total_lat,
            "error": None
        }
    except Exception as err:
        logger.error(f"[WorkerTask] Failed processing photo {photo_id}: {err}")
        return {
            "photo_id": photo_id,
            "project_id": project_id,
            "success": False,
            "has_face": False,
            "review_needed": True,
            "review_reason": f"Processing failure: {str(err)}",
            "latency_ms": max(1, int((time.time() - start_time) * 1000)),
            "error": str(err)
        }


def run_bulk_project_processing(
    project_id: str,
    photo_ids: List[str],
    custom_settings: Optional[Dict[str, Any]] = None,
    progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
    max_workers: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Executes bulk processing across ProcessPoolExecutor workers.
    Calls progress_callback(processed_count, total_count, result) per photo.
    """
    workers = max_workers or min(max(1, (os.cpu_count() or 2) - 1), 8)
    total = len(photo_ids)
    results = []

    logger.info(f"[WorkerPool] Spawning {workers} workers for {total} photos in project {project_id}")

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=init_worker_process
    ) as executor:
        futures = {
            executor.submit(process_single_photo_task, project_id, pid, custom_settings): pid
            for pid in photo_ids
        }

        processed = 0
        for future in as_completed(futures):
            pid = futures[future]
            try:
                task_res = future.result()
            except Exception as task_exc:
                task_res = {
                    "photo_id": pid,
                    "project_id": project_id,
                    "success": False,
                    "review_needed": True,
                    "error": str(task_exc),
                    "latency_ms": 0
                }

            results.append(task_res)
            processed += 1
            if progress_callback:
                progress_callback(processed, total, task_res)

    return results
