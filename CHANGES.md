# PhotoBulk (KameraPh) - Architecture, Hardening & Quality Verification (Phases 0-6)

This document summarizes the systematic hardening and stabilization of PhotoBulk (KameraPh) for a single studio processing 300 to 500 graduation portrait photos locally per project (`Projects` -> `Upload` -> `Review` -> `Editor` -> `Apply to all` -> `Export`).

---

## Phase 0: Environment & Tests
- **Python 3.12 Compatibility**: Updated `requirements.txt` and `README.md` to specify Python 3.12, added `google-genai` library, and ensured modern dependency resolution.
- **Isolated Test Data Directory**: Replaced hardcoded `local_data` paths in test runs with dynamic temporary directories (`tmp_path`) managed via `config.DATA_DIR`. The active studio store is never touched during testing.
- **Real Portrait Test Fixtures**: Removed synthetic cartoon fixtures. Standardized test suites on scikit-image's standard astronaut portrait (`skimage.data.astronaut()`) containing real human skin, facial structures, and detectable landmarks for both Haar cascade and YuNet ONNX detectors.
- **BiSeNet Fallback Safety**: Added graceful degradation when `bisenet_face_parsing.onnx` is missing, falling back smoothly to geometric/ellipse facial masking without crash or HTTP 500.

## Phase 1: Security Basics
- **Identifier Validation & Path Traversal Defense**: Enforced strict regex pattern matching (`^[a-zA-Z0-9_\-]+$`) on `project_id`, `photo_id`, and `job_id` parameters across all API endpoints, preventing path traversal attacks (`../`, `%2e%2e/`).
- **Studio Tenant Isolation**: Enforced multi-tenant isolation where non-admin studio users can only list, view, modify, or export projects belonging to their own `studio_id`.
- **JWT Secret Startup Refusal**: Implemented startup guard in `config.py` / `api_server.py` rejecting placeholder JWT secrets (`"your-secret-key-change-in-production"`) in production environments (`ENVIRONMENT=production`).
- **Secure Password Hashing**: Upgraded password hashing and verification using `bcrypt` directly with salted key derivation.

## Phase 2: Upload That Scales
- **Chunked & Streaming Multi-Part Upload**: Implemented chunked disk-buffered streaming in `save_uploaded_photo` avoiding in-memory byte accumulation and OOM crashes when uploading 300-500 high-res camera originals (10-25 MB each).
- **EXIF & ICC Profile Preservation**: Retained raw metadata, EXIF orientation, and color space tags upon upload to prevent color shift between camera RAW/sRGB previews and print outputs.
- **Background Worker Task Offloading**: Shifted facial landmark analysis, exposure metric calculation, and thumbnail generation to background workers (`WorkerPool`), keeping the upload endpoint snappy.
- **Nginx Configuration**: Configured client max body size to `150M` in `nginx.conf`.

## Phase 3: Pipeline & Memory Streamlining
- **Eliminated Legacy In-Memory Cache**: Removed deprecated `batch_store` in-memory structures and legacy pipeline artifacts.
- **Disk-as-Single-Source-of-Truth**: Anchored all state, photo settings, previews, and exports in `local_data/projects/{project_id}`.
- **On-Demand Master Loading**: Avoided keeping full-resolution 24-48 megapixel image arrays resident in RAM. Full master images are loaded on-demand, processed, and immediately garbage-collected.

## Phase 4: Jobs That Survive Server Restarts
- **Persistent SQLite Job Store**: Enabled SQLite Write-Ahead Logging (WAL) mode with concurrency locks.
- **Restart Crash Recovery**: Added `recover_interrupted_jobs()` in `init_db.py`, which scans for any unfinished jobs (`queued`, `running`, `processing`) upon server startup and marks them `failed` with descriptive restart recovery notes instead of hanging indefinitely.
- **Direct Job Polling**: Updated `GET /api/jobs/{job_id}` to query the SQLite table directly.
- **Single-Worker Execution Model**: Documented and configured `--workers 1` in `Dockerfile` and `start.sh` for predictable local background task execution without split-process memory states.

## Phase 5: Apply to All and Export
- **Non-Blocking Apply-to-All**: `POST /api/projects/{project_id}/photos/{source_photo_id}/apply-to-all` copies settings across photos instantly, creates a tracking job, and executes preview re-rendering across worker threads.
- **Parallel High-Resolution Export**: Implemented `ThreadPoolExecutor` parallelization in `export_engine.py` for full-resolution rendering and print packaging.
- **Collision-Free Filename Resolution**: Resolved duplicate student names deterministically with numeric suffixes (`_2`, `_3`, etc.) while recording both canonical and resolved filenames in `EXPORT_MANIFEST.txt`.
- **Print Safety (300 DPI Validation)**: Added proactive DPI warning checks against target print dimensions (e.g., 8R, 5R), recording low-res warnings into the export manifest and returning them via API response.
- **Frontend Sync**: Updated frontend React state (`App.tsx`, `apiClient.ts`) to poll apply-to-all jobs and smoothly update photo cards.

## Phase 6: Output Quality & Print Specifications
- **PRC/DFA 2x2 Compliance**:
  - Official DFA/PRC specifications require a plain white background with 70-80% head height ratio.
  - Updated `crop_2x2_id` in `pipeline.py` to composite the subject onto pure white (`white_background=True`, corner pixels $\ge 245$) using the segmented alpha matte.
  - Uses original un-smoothed photo pixels without facial reshaping or synthetic smoothing, strictly complying with government ID standards.
- **Smart Auto-Exposure**:
  - Refined EV compensation factor scaling (`np.clip(2.0 ** ev, 0.50, 2.80)`) to lift underexposed portraits into the optimal facial luminance range ($L^* \in [52, 72]$) without washing out highlights.
- **Strict Preset & Backdrop Validation**:
  - Standardized default presets to valid catalog entries (`"natural"` preset and `"classic_blue"` backdrop).
  - Enforced 400 Bad Request rejection in `update_photo_settings` for unknown preset or backdrop IDs, preserving studio configuration integrity.
- **Automated Verification Suite**:
  - Added `test_36_phase6_output_quality_exposure_and_specs`.
  - All 36 automated tests across the test suite pass with 100% success (0 failures, 0 skips).
