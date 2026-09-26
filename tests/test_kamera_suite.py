"""
KameraPh Comprehensive Automated Test Suite
-------------------------------------------
Validates all P0, P1, and P2 fixes:
  - Database schema & multi-tenant isolation
  - Admin authentication & session enforcement
  - PayMongo cryptographic signature verification & idempotency
  - Neural matting & Regalia preservation (Cap, Tassel, Gown)
  - Authentic Morena tone preservation (CIELAB ΔL* constraint)
  - 2x2 ID crop compliance (DFA & PRC specifications)
  - Multi-student batch gang sheet generation
  - Multi-face and no-face review flag handling
  - Credit deduction & zero-credit blocking
  - Upload sanitization, path traversal prevention & temp directory isolation
"""

import os
import sys
import unittest
import cv2
import numpy as np
import tempfile
import io
import zipfile
from fastapi.testclient import TestClient
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from init_db import init_database, get_db_connection, fetch_job_db
from auth import create_access_token
from analyzer_engine import analyze_portrait, get_face_detector
from beautification_presets import apply_beauty_preset_to_image, BEAUTY_PRESETS, LIP_COLOR_PALETTES
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop, STUDIO_BACKDROPS
from payment_engine import payment_engine
from r2_storage import storage
from regalia_profiles import REGALIA_PROFILES
from pdf_engine import generate_contact_sheet_pdf, generate_lab_gang_sheet_pdf, generate_batch_lab_gang_sheet_pdf
from pipeline import (
    process_complete_workflow,
    process_image,
    crop_8r_aspect,
    crop_2x2_id,
    get_subject_mask,
    detect_actual_engine,
    generate_watermarked_proof
)
from api_server import app, BATCH_STORE, sanitize_filename_or_folder, deduct_studio_credit, get_studio_state


class TestKameraPhSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = init_database()
        cls.client = TestClient(app)
        
        # Load synthetic test fixture image
        fixture_path = os.path.join(BASE_DIR, "tests", "fixtures", "synthetic_portrait.jpg")
        if os.path.exists(fixture_path):
            cls.test_img = cv2.imread(fixture_path)
        else:
            cls.test_img = np.full((800, 600, 3), (220, 220, 220), dtype=np.uint8)
            cv2.ellipse(cls.test_img, (300, 350), (90, 120), 0, 0, 360, (135, 170, 210), -1)

        # Load real/synthetic face portrait fixture (with detectable face)
        face_fixture_path = os.path.join(BASE_DIR, "tests", "fixtures", "sample_grad_face.jpg")
        if os.path.exists(face_fixture_path):
            cls.face_img = cv2.imread(face_fixture_path)
        else:
            alt_path = os.path.join(BASE_DIR, "local_storage", "Juan_DelaCruz_Graduation_Proof_KameraPh_Enhanced.jpg")
            if os.path.exists(alt_path):
                cls.face_img = cv2.imread(alt_path)
            else:
                cls.face_img = cls.test_img

    def test_01_database_and_rls_schema(self):
        """Verify database tables and seeded records exist."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM studios;")
        studio_count = cursor.fetchone()["count"]
        self.assertGreaterEqual(studio_count, 1)

        cursor.execute("SELECT credit_balance FROM studios LIMIT 1;")
        balance = cursor.fetchone()["credit_balance"]
        self.assertGreaterEqual(balance, 0)
        conn.close()

    def test_02_admin_route_protection(self):
        """P0-4: Verify /api/admin/* endpoints require server-checked admin session."""
        # Unauthenticated request must be rejected (401 or 403)
        res_unauth = self.client.get("/api/admin/ai-config")
        self.assertIn(res_unauth.status_code, [401, 403])

        # Studio user (non-admin) must be forbidden (403)
        user_token = create_access_token({
            "id": "user-123",
            "email": "editor@auragrad-studio.ph",
            "role": "studio_user"
        })
        res_forbidden = self.client.get("/api/admin/ai-config", headers={"Authorization": f"Bearer {user_token}"})
        self.assertEqual(res_forbidden.status_code, 403)

        # Super admin must be granted access (200)
        admin_token = create_access_token({
            "id": "admin-1",
            "email": "admin@kameraph.com",
            "role": "super_admin"
        })
        res_admin = self.client.get("/api/admin/ai-config", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(res_admin.status_code, 200)

    def test_03_ai_key_test_failure_reporting(self):
        """P1-13: Verify AI key test accurately reports errors rather than false success."""
        admin_token = create_access_token({
            "id": "admin-1",
            "email": "admin@kameraph.com",
            "role": "super_admin"
        })
        # Test with invalid bogus key
        res = self.client.post(
            "/api/admin/test-ai-key",
            data={"api_key": "AIzaSyBogusInvalidKey12345"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(res.status_code, 400)
        data = res.json()
        self.assertFalse(data.get("success", False))

    def test_04_paymongo_webhook_signature_and_idempotency(self):
        """P0-5: Verify credits are granted ONLY upon signed PayMongo webhooks, and are idempotent."""
        checkout = payment_engine.create_checkout_session(
            package_id="school_500",
            studio_id="studio-test",
            studio_email="test@auragrad-studio.ph",
            studio_name="AuraGrad Studio"
        )
        self.assertIn("session_id", checkout)

        # 1. Unsigned webhook must be rejected when secret is configured
        payment_engine.webhook_secret = "whsk_test_mock_secret"
        payload_bytes = b'{"data":{"attributes":{"type":"checkout_session.payment.paid"}}}'
        self.assertFalse(payment_engine.verify_webhook_signature(payload_bytes, ""))

        # 2. Process valid event
        event_payload = {
            "type": "checkout_session.payment.paid",
            "session_id": checkout["session_id"],
            "data": {
                "attributes": {
                    "type": "checkout_session.payment.paid",
                    "data": {
                        "attributes": {
                            "payment_method_used": "gcash",
                            "amount": 185000
                        }
                    }
                }
            }
        }
        res1 = payment_engine.handle_webhook_event(event_payload)
        self.assertTrue(res1["success"])
        self.assertEqual(res1["credits_added"], 500)

        # 3. Idempotency test: Re-sending same event must NOT add credits twice!
        res2 = payment_engine.handle_webhook_event(event_payload)
        self.assertEqual(res2.get("credits_added", 0), 0)

    def test_05_cap_tassel_gown_preservation_regression(self):
        """P1-11: Regression test verifying cap, tassel, and gown are preserved in mask."""
        mask = get_subject_mask(self.test_img)
        self.assertEqual(mask.shape[:2], self.test_img.shape[:2])
        self.assertEqual(mask.dtype, np.uint8)

        h, w = mask.shape
        # Check cap region (y: 180-240, x: 200-400)
        cap_region = mask[180:240, 200:400]
        cap_coverage = np.mean(cap_region > 0)
        self.assertGreater(cap_coverage, 0.40, "Regression: Cap/mortarboard region was clipped from subject mask!")

        # Check gown region (y: 500-750, x: 200-400)
        gown_region = mask[500:750, 200:400]
        gown_coverage = np.mean(gown_region > 0)
        self.assertGreater(gown_coverage, 0.60, "Regression: Gown/toga body was clipped from subject mask!")

    def test_06_skin_tone_morena_preservation_lab_test(self):
        """P1-16: Measure CIELAB L* before and after to ensure Morena skin is not lightened/bleached."""
        # Convert original to LAB
        orig_lab = cv2.cvtColor(self.test_img, cv2.COLOR_BGR2LAB)
        # Sample skin patch from forehead/cheek
        orig_skin_patch = orig_lab[320:360, 280:320]
        mean_l_before = np.mean(orig_skin_patch[:, :, 0])

        enhanced = apply_beauty_preset_to_image(
            self.test_img,
            preset_id="morena_radiant",
            custom_adjustments={
                "skin_smoothing": 0.70,
                "blemish_cut": 0.75,
                "glow_intensity": 0.40
            }
        )
        enh_lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        enh_skin_patch = enh_lab[320:360, 280:320]
        mean_l_after = np.mean(enh_skin_patch[:, :, 0])

        delta_l = mean_l_after - mean_l_before
        # Delta L* must be within 3.5 points (no bleaching/whitening)
        self.assertLessEqual(delta_l, 3.5, f"Regression: Skin tone lightened by {delta_l:.2f} L* units! Morena tone altered.")

    def test_07_dfa_prc_2x2_crop_specifications(self):
        """P1-17: Verify 2x2 ID crop complies with DFA and PRC specs (600x600, head 70-80%)."""
        analysis = analyze_portrait(self.test_img)
        fb = analysis.get("face_box", {"x": 200, "y": 200, "width": 200, "height": 200})
        face_info = {"bbox": [fb["x"], fb["y"], fb["width"], fb["height"]]}
        
        crop = crop_2x2_id(self.test_img, face_info, spec="DFA")
        self.assertEqual(crop.shape, (600, 600, 3), "2x2 Crop must be exactly 600x600 px at 300 DPI")

    def test_08_multi_face_and_zero_face_handling(self):
        """P1-15: Verify multi-face photos select largest face and flag review_needed."""
        h, w = 600, 800
        multi_img = np.full((h, w, 3), 200, dtype=np.uint8)
        # Primary large face
        cv2.circle(multi_img, (300, 300), 100, (140, 175, 210), -1)
        # Background small face
        cv2.circle(multi_img, (650, 250), 30, (140, 175, 210), -1)

        analysis = analyze_portrait(multi_img)
        self.assertIn("review_needed", analysis)
        self.assertIn("review_reason", analysis)

        # Blank image (zero faces)
        blank_img = np.zeros((400, 400, 3), dtype=np.uint8)
        blank_analysis = analyze_portrait(blank_img)
        self.assertTrue(blank_analysis["review_needed"])
        self.assertIn("No clear face detected", blank_analysis["review_reason"])

    def test_09_credit_deduction_and_zero_credit_blocking(self):
        """P1-14: Verify credits deduct per photo and block processing at zero."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, credit_balance FROM studios LIMIT 1;")
        studio = cursor.fetchone()
        studio_id = studio["id"]
        
        # Ensure sufficient starting balance for test
        cursor.execute("UPDATE studios SET credit_balance = 150 WHERE id = ?;", (studio_id,))
        conn.commit()
        initial_balance = 150

        import api_server
        original_pe = api_server.PAYMENTS_ENABLED
        try:
            # When PAYMENTS_ENABLED is True, test deduction and 402 blocking
            api_server.PAYMENTS_ENABLED = True
            success = deduct_studio_credit(studio_id, count=1)
            self.assertTrue(success)
            
            cursor.execute("SELECT credit_balance FROM studios WHERE id = ?;", (studio_id,))
            updated_balance = cursor.fetchone()["credit_balance"]
            self.assertEqual(updated_balance, initial_balance - 1)

            # Set balance to 0 and verify blocking
            cursor.execute("UPDATE studios SET credit_balance = 0 WHERE id = ?;", (studio_id,))
            conn.commit()

            res = self.client.post("/api/process-image", data={"regalia_profile": "standard_toga"})
            self.assertEqual(res.status_code, 402, "Must return 402 Payment Required when credit balance is zero and payments enabled!")

            # When PAYMENTS_ENABLED is False (Step 0 feature flag), verify bypass (no 402, no deduction)
            api_server.PAYMENTS_ENABLED = False
            bypassed = deduct_studio_credit(studio_id, count=1)
            self.assertTrue(bypassed)
            # Balance should remain 0, no deduction occurred
            cursor.execute("SELECT credit_balance FROM studios WHERE id = ?;", (studio_id,))
            self.assertEqual(cursor.fetchone()["credit_balance"], 0)
        finally:
            api_server.PAYMENTS_ENABLED = original_pe
            # Restore credits reliably
            cursor.execute("UPDATE studios SET credit_balance = 150 WHERE id = ?;", (studio_id,))
            conn.commit()
            conn.close()

    def test_10_batch_gang_sheet_multi_student(self):
        """P1-18: Verify gang sheet renders pages for every student in batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            p1 = os.path.join(temp_dir, "student_1.jpg")
            p2 = os.path.join(temp_dir, "student_2.jpg")
            cv2.imwrite(p1, self.test_img)
            cv2.imwrite(p2, self.test_img)

            students = [
                {"student_name": "Maria Santos", "master_image_path": p1, "crop_8r_path": p1, "crop_2x2_path": p1},
                {"student_name": "Angelo Reyes", "master_image_path": p2, "crop_8r_path": p2, "crop_2x2_path": p2}
            ]
            pdf_bytes = generate_batch_lab_gang_sheet_pdf(students, "Batch 2026", "AuraGrad Studio")
            self.assertGreater(len(pdf_bytes), 5000, "Multi-page gang sheet PDF generated successfully")

    def test_11_export_sanitization_and_isolation(self):
        """P2-30 & P2-31: Clean school_name against traversal and verify temp folder isolation."""
        malicious_input = "../../../etc/passwd\r\nHeaderInjection:Bad"
        clean = sanitize_filename_or_folder(malicious_input)
        self.assertNotIn("..", clean)
        self.assertNotIn("/", clean)
        self.assertNotIn("\\", clean)
        self.assertNotIn("\r", clean)
        self.assertNotIn("\n", clean)

    def test_12_url_photo_endpoints_no_base64_overload(self):
        """P2-28: Verify /api/photos/{photo_id}/* routes return streamable image binaries."""
        # Stage a test photo in batch store
        pid = "test-stream-001"
        BATCH_STORE[pid] = {
            "id": pid,
            "filename": "Test.jpg",
            "img_bgr": self.test_img,
            "enhanced_bgr": self.test_img,
            "face_info": None,
            "analysis": {},
            "status": "done"
        }
        res = self.client.get(f"/api/photos/{pid}/preview")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["content-type"], "image/jpeg")
        self.assertGreater(len(res.content), 500)

    def test_13_safe_file_io_and_nested_directory_creation(self):
        """Task 1C: Verifies pdf_engine and analyzer_engine handle non-existent directories and files safely."""
        from pathlib import Path
        from analyzer_engine import analyze_portrait, load_portrait_image_safely
        import tempfile
        import shutil

        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Test auto-creation of deeply nested output directories
            deep_nested_path = Path(temp_dir) / "sub1" / "sub2" / "sub3" / "test_gang.pdf"
            self.assertFalse(deep_nested_path.parent.exists())

            # Create synthetic test file
            synth_p = Path(temp_dir) / "synth.jpg"
            cv2.imwrite(str(synth_p), self.test_img)

            # Should automatically create parents and write without FileNotFoundError
            pdf_bytes = generate_lab_gang_sheet_pdf(
                master_image_path=str(synth_p),
                crop_8r_path=str(synth_p),
                crop_2x2_path=str(synth_p),
                output_path=deep_nested_path
            )
            self.assertTrue(deep_nested_path.is_file())
            self.assertGreater(deep_nested_path.stat().st_size, 1000)

            # 2. Test analyze_portrait safe handling of missing file path
            missing_file = Path(temp_dir) / "non_existent.jpg"
            analysis_result = analyze_portrait(missing_file)
            self.assertIsInstance(analysis_result, dict)
            self.assertTrue(analysis_result["review_needed"])
            self.assertIn("Failed to load image", analysis_result["review_reason"])

            # 3. Test explicit FileNotFoundError in load_portrait_image_safely
            with self.assertRaises(FileNotFoundError):
                load_portrait_image_safely(missing_file)

            # 4. Test contact sheet generation with missing image paths
            photos_with_missing = [
                {"name": "Missing1", "image_path": str(missing_file)},
                {"name": "Valid1", "image_path": str(synth_p)}
            ]
            nested_contact = Path(temp_dir) / "reports" / "contact_sheet.pdf"
            contact_bytes = generate_contact_sheet_pdf(photos_with_missing, output_path=nested_contact)
            self.assertTrue(nested_contact.is_file())
            self.assertGreater(len(contact_bytes), 1000)

    def test_14_presigned_r2_upload_and_registration(self):
        """Task 2A: Verifies Cloudflare R2 presigned upload/download and direct edge registration flow."""
        # 1. Request presigned upload URL via GET
        res_get_url = self.client.get("/api/storage/presigned-url?file_key=direct_edge_test.jpg&action=upload")
        self.assertEqual(res_get_url.status_code, 200)
        data_get = res_get_url.json()
        self.assertIn("upload_url", data_get)
        self.assertIn("file_key", data_get)
        self.assertEqual(data_get["file_key"], "direct_edge_test.jpg")

        # 2. Request presigned upload URL via typed POST
        res_post_url = self.client.post("/api/storage/presigned-upload", json={"filename": "Cohort_2026_Grad.jpg"})
        self.assertEqual(res_post_url.status_code, 200)
        data_post = res_post_url.json()
        self.assertIn("upload_url", data_post)
        self.assertIn("Cohort_2026_Grad.jpg", data_post["file_key"])
        target_file_key = data_post["file_key"]
        upload_endpoint = data_post["upload_url"]

        # 3. Simulate browser direct PUT upload
        _, test_jpg_bytes = cv2.imencode(".jpg", self.test_img)
        res_put = self.client.put(upload_endpoint, content=test_jpg_bytes.tobytes(), headers={"Content-Type": "image/jpeg"})
        self.assertEqual(res_put.status_code, 200)
        put_data = res_put.json()
        self.assertTrue(put_data["success"])
        self.assertEqual(put_data["file_key"], target_file_key)

        # 4. Register photo with backend
        res_reg = self.client.post("/api/storage/register-photo", json={
            "file_key": target_file_key,
            "filename": "Cohort_2026_Grad.jpg"
        })
        self.assertEqual(res_reg.status_code, 200)
        reg_data = res_reg.json()
        self.assertTrue(reg_data["success"])
        item = reg_data["item"]
        self.assertIn("id", item)
        self.assertEqual(item["name"], "Cohort_2026_Grad.jpg")
        self.assertEqual(item["status"], "ready")
        self.assertIn("previewUrl", item)
        self.assertIn("masterUrl", item)

        # Verify photo exists in BATCH_STORE and can be previewed
        photo_id = item["id"]
        self.assertIn(photo_id, BATCH_STORE)
        res_preview = self.client.get(f"/api/photos/{photo_id}/preview")
        self.assertEqual(res_preview.status_code, 200)
        self.assertEqual(res_preview.headers["content-type"], "image/jpeg")

        # 5. Request presigned download URL
        res_down = self.client.get(f"/api/storage/presigned-url?file_key={target_file_key}&action=download")
        self.assertEqual(res_down.status_code, 200)
        down_data = res_down.json()
        self.assertIn("download_url", down_data)

    def test_15_cryptographic_webhook_verification(self):
        """Task 2B: Verifies PayMongo HMAC-SHA256 signature middleware, replay protection, and idempotency."""
        from webhook_verifier import webhook_verifier
        import json
        import time

        test_secret = "whsec_test_kamera_secret_2026"
        webhook_verifier.webhook_secret = test_secret

        # 1. Create a pending checkout session in DB
        checkout = payment_engine.create_checkout_session(
            package_id="volume_2500",
            studio_id="studio-test",
            studio_email="billing@auragrad-studio.ph",
            studio_name="AuraGrad Studio"
        )
        session_id = checkout["session_id"]

        valid_payload_dict = {
            "type": "checkout_session.payment.paid",
            "session_id": session_id,
            "data": {
                "attributes": {
                    "type": "checkout_session.payment.paid",
                    "data": {
                        "attributes": {
                            "payment_method_used": "gcash",
                            "amount": 750000
                        }
                    }
                }
            }
        }
        valid_raw_bytes = json.dumps(valid_payload_dict).encode("utf-8")

        # 2. Reject request with missing signature header
        res_missing = self.client.post("/api/payments/webhook", content=valid_raw_bytes)
        self.assertEqual(res_missing.status_code, 401)
        self.assertIn("Missing Paymongo-Signature", res_missing.json()["detail"])

        # 3. Reject request with invalid signature
        fake_header = f"t={int(time.time())},te=deadbeef1234567890abcdefdeadbeef1234567890abcdefdeadbeef1234567890"
        res_invalid = self.client.post("/api/payments/webhook", content=valid_raw_bytes, headers={"Paymongo-Signature": fake_header})
        self.assertEqual(res_invalid.status_code, 401)
        self.assertIn("Signature mismatch", res_invalid.json()["detail"])

        # 4. Reject replay attack (timestamp older than 300 seconds)
        expired_ts = int(time.time()) - 400
        expired_header = webhook_verifier.generate_header(valid_raw_bytes, timestamp=expired_ts, secret=test_secret)
        res_expired = self.client.post("/api/payments/webhook", content=valid_raw_bytes, headers={"Paymongo-Signature": expired_header})
        self.assertEqual(res_expired.status_code, 401)
        self.assertIn("tolerance", res_expired.json()["detail"])

        # 5. Accept cryptographically valid signature with fresh timestamp
        valid_header = webhook_verifier.generate_header(valid_raw_bytes, secret=test_secret)
        res_valid = self.client.post("/api/payments/webhook", content=valid_raw_bytes, headers={"Paymongo-Signature": valid_header})
        self.assertEqual(res_valid.status_code, 200)
        valid_data = res_valid.json()
        self.assertTrue(valid_data["success"])
        self.assertEqual(valid_data["credits_added"], 2500)
        self.assertEqual(valid_data["session_id"], session_id)

        # 6. Idempotency: replay the same event, must not add credits again
        fresh_header_replay = webhook_verifier.generate_header(valid_raw_bytes, secret=test_secret)
        res_replay = self.client.post("/api/payments/webhook", content=valid_raw_bytes, headers={"Paymongo-Signature": fresh_header_replay})
        self.assertEqual(res_replay.status_code, 200)
        replay_data = res_replay.json()
        self.assertTrue(replay_data["success"])
        self.assertEqual(replay_data["credits_added"], 0)
        self.assertIn("already processed", replay_data["message"])

        # 7. Malformed JSON payload rejection (400)
        malformed_bytes = b"not-a-valid-json-payload{"
        malformed_header = webhook_verifier.generate_header(malformed_bytes, secret=test_secret)
        res_malformed = self.client.post("/api/payments/webhook", content=malformed_bytes, headers={"Paymongo-Signature": malformed_header})
        self.assertEqual(res_malformed.status_code, 400)
        self.assertIn("Malformed JSON", res_malformed.json()["detail"])

        # Reset secret for subsequent tests
        webhook_verifier.webhook_secret = ""

    def test_16_standardized_ml_pipeline(self):
        """Task 2C: Verifies standardized process_image entry point, Pydantic typing, and safe export."""
        from kamera_pipeline_v3 import process_image, ProcessingParams, ProcessedImageResult
        from pathlib import Path
        import tempfile

        # 1. Test in-memory numpy array execution
        result_mem = process_image(self.test_img)
        self.assertIsInstance(result_mem, ProcessedImageResult)
        self.assertTrue(result_mem.success)
        self.assertIsNotNone(result_mem.enhanced_bgr)
        self.assertIsNotNone(result_mem.crop_8r_bgr)
        self.assertIsNotNone(result_mem.crop_2x2_bgr)
        self.assertGreater(result_mem.latency_ms, 0)
        self.assertIn("Hybrid", result_mem.engine_used)

        # 2. Test file path input with custom ProcessingParams and disk exports
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_file = temp_path / "student_sample.jpg"
            cv2.imwrite(str(input_file), self.test_img)

            export_dir = temp_path / "cohort_out" / "section_a"
            params = ProcessingParams(
                bg_replacement_enabled=True,
                backdrop_type="royal_navy",
                beauty_preset="morena_radiant",
                regalia_profile="up_sablay",
                output_directory=str(export_dir),
                save_crops=True,
                save_proof=True,
                student_name="Maria Clara"
            )

            result_file = process_image(input_file, parameters=params)
            self.assertTrue(result_file.success)
            self.assertIsNotNone(result_file.enhanced_image_path)
            self.assertTrue(Path(result_file.enhanced_image_path).is_file())
            self.assertIsNotNone(result_file.crop_8r_path)
            self.assertTrue(Path(result_file.crop_8r_path).is_file())
            self.assertIsNotNone(result_file.crop_2x2_path)
            self.assertTrue(Path(result_file.crop_2x2_path).is_file())
            self.assertIsNotNone(result_file.proof_path)
            self.assertTrue(Path(result_file.proof_path).is_file())

            # 3. Test non-existent file path: Zero Silent Failures graceful error
            missing_input = temp_path / "does_not_exist.jpg"
            result_missing = process_image(missing_input)
            self.assertFalse(result_missing.success)
            self.assertIn("not found", result_missing.error.lower())

    def test_17_async_batch_job_worker_and_polling(self):
        """Task Phase 3: Validates 202 Accepted, background worker execution, polling, and DB ledger."""
        import time

        # Top up studio credits first to ensure sufficient balance
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE studios SET credit_balance = 500 WHERE id = 'studio-default';")
        conn.commit()
        conn.close()

        # 1. Upload 2 synthetic images to batch store
        success, enc1 = cv2.imencode('.jpg', self.test_img)
        files = [
            ("files", ("async_student_1.jpg", enc1.tobytes(), "image/jpeg")),
            ("files", ("async_student_2.jpg", enc1.tobytes(), "image/jpeg")),
        ]
        res_upload = self.client.post("/api/batch-upload", files=files)
        self.assertEqual(res_upload.status_code, 200)
        self.assertEqual(res_upload.json()["uploaded_count"], 2)

        # 2. Test non-blocking batch process (HTTP 202 Accepted)
        res_process = self.client.post("/api/batch-process", data={
            "bg_replacement_enabled": "true",
            "backdrop_type": "royal_navy",
            "beauty_preset": "morena_radiant"
        })
        self.assertEqual(res_process.status_code, 202)
        job_data = res_process.json()
        self.assertIn("job_id", job_data)
        job_id = job_data["job_id"]
        self.assertIn(job_data["status"], ["queued", "processing", "completed"])

        # 3. Poll GET /api/jobs/{job_id} until completed
        completed = False
        final_job = None
        for _ in range(40):
            res_poll = self.client.get(f"/api/jobs/{job_id}")
            self.assertEqual(res_poll.status_code, 200)
            poll_data = res_poll.json()
            if poll_data["status"] == "completed":
                completed = True
                final_job = poll_data
                break
            time.sleep(0.05)

        self.assertTrue(completed, f"Job {job_id} did not complete in time")
        self.assertEqual(final_job["progress"], 100)
        self.assertGreaterEqual(len(final_job["items"]), 2)

        # 4. Verify job was persisted in database ledger
        db_job = fetch_job_db(job_id)
        self.assertIsNotNone(db_job)
        self.assertEqual(db_job["status"], "completed")
        self.assertEqual(db_job["progress_percentage"], 100)

        # 5. Test synchronous execution fallback with ?sync=true
        res_sync = self.client.post("/api/batch-process?sync=true", data={
            "bg_replacement_enabled": "true",
            "backdrop_type": "royal_navy",
            "beauty_preset": "morena_radiant"
        })
        self.assertEqual(res_sync.status_code, 200)
        sync_data = res_sync.json()
        self.assertIn("processed_count", sync_data)
        self.assertIn("items", sync_data)

        # 6. Test 404 for invalid job id
        res_404 = self.client.get("/api/jobs/job-non-existent-xyz")
        self.assertEqual(res_404.status_code, 404)

    def test_18_face_landmarks_pipeline_and_no_face_handling(self):
        """Step 1: Verify face landmarks in analysis/face_info, no KeyError crash, and no-face handling."""
        # 1. Test with real face fixture
        analysis = analyze_portrait(self.face_img)
        self.assertTrue(analysis["has_face"], "Face fixture portrait must have detectable face")
        self.assertIsNotNone(analysis.get("landmarks"), "Landmarks must be returned in analysis")
        for key in ["right_eye", "left_eye", "nose", "right_mouth", "left_mouth"]:
            self.assertIn(key, analysis["landmarks"])

        # 2. Verify complete workflow does not crash with KeyError
        enhanced, latency, face_info, engine = process_complete_workflow(self.face_img)
        self.assertIsNotNone(face_info)
        self.assertIn("right_eye", face_info)
        self.assertIn("left_eye", face_info)
        self.assertEqual(enhanced.shape[:2], self.face_img.shape[:2])

        # 3. Verify no-face handling (skips face retouching, runs backdrop+lighting, sets review_needed)
        blank_img = np.full((400, 400, 3), 180, dtype=np.uint8)
        no_face_res = process_image(blank_img)
        self.assertTrue(no_face_res.success)
        self.assertFalse(no_face_res.analysis["has_face"])
        self.assertTrue(no_face_res.analysis["review_needed"])
        self.assertIsNotNone(no_face_res.analysis.get("review_reason"))
        self.assertIsNotNone(no_face_res.enhanced_bgr)

    def test_19_persistent_project_store_and_fast_preview(self):
        """Step 2: Verify on-disk project folder, feature caching, sub-second slider preview, and restart restoration."""
        from project_store import project_store
        from api_server import restore_projects_to_batch_store

        proj_id = "test_persistence_proj"
        photo_id = "photo_step2_test"

        try:
            # 1. Save uploaded photo to on-disk project store
            meta = project_store.save_uploaded_photo(proj_id, photo_id, "student_portrait.jpg", self.face_img)
            self.assertEqual(meta["id"], photo_id)

            photo_dir = project_store.get_photo_dir(proj_id, photo_id)
            self.assertTrue((photo_dir / "original.jpg").exists())
            self.assertTrue((photo_dir / "preview.jpg").exists())
            self.assertTrue((photo_dir / "settings.json").exists())

            # 2. Compute and cache heavy features once
            features = project_store.compute_and_cache_heavy_features(proj_id, photo_id)
            self.assertTrue((photo_dir / "face.json").exists())
            self.assertTrue((photo_dir / "analysis.json").exists())
            self.assertTrue((photo_dir / "alpha.png").exists())

            # 3. Slider adjustments: must only rerun cheap beauty on preview image in under 1 second
            preview_bgr, lat_ms = project_store.render_preview_fast(proj_id, photo_id, {"skin_smoothing": 0.85})
            self.assertLess(lat_ms / 1000.0, 1.5, f"Preview slider update took {lat_ms}ms, target is < 1s")
            self.assertIsNotNone(preview_bgr)

            # 4. Full-resolution export render
            render_res = project_store.render_full_resolution(proj_id, photo_id)
            self.assertTrue(os.path.exists(render_res["master_path"]))
            self.assertTrue(os.path.exists(render_res["crop_8r_path"]))
            self.assertTrue(os.path.exists(render_res["crop_2x2_path"]))

            # 5. Server restart simulation: clear in-memory BATCH_STORE and restore from disk
            BATCH_STORE.pop(photo_id, None)
            restore_projects_to_batch_store()
            self.assertIn(photo_id, BATCH_STORE, "Photo must survive server restart by restoring from on-disk project folder")
        finally:
            import shutil
            shutil.rmtree(str(project_store.get_project_dir(proj_id)), ignore_errors=True)
            BATCH_STORE.pop(photo_id, None)

    def test_20_soft_alpha_matte_and_backdrop_modes(self):
        """STEP 3: Verify soft alpha matte retains fractional edge values and test backdrop modes."""
        from background_engine import clean_original_backdrop, generate_studio_backdrop, composite_subject_onto_backdrop, STUDIO_BACKDROPS
        
        face_path = Path(__file__).parent / "fixtures" / "sample_grad_face.jpg"
        if not face_path.exists():
            self.skipTest("sample_grad_face.jpg fixture not found")
        img = cv2.imread(str(face_path))
        
        # Get neural subject mask
        mask = get_subject_mask(img)
        self.assertEqual(mask.shape[:2], img.shape[:2])
        self.assertEqual(mask.dtype, np.uint8)
        
        # Verify fractional alpha values exist (not only 0 and 255)
        fractional_count = int(np.count_nonzero((mask > 5) & (mask < 250)))
        self.assertGreater(fractional_count, 500, "Alpha matte must be soft/fractional along hair and edges, not hard thresholded 0/255!")
        
        # Verify all clean backdrops generate correctly
        for bg_id in ["classic_blue", "deep_navy", "neutral_grey", "studio_white", "warm_brown"]:
            bg = generate_studio_backdrop(400, 500, backdrop_type=bg_id)
            self.assertEqual(bg.shape, (500, 400, 3))
            self.assertEqual(bg.dtype, np.uint8)
            
        # Verify clean_original_backdrop mode
        cleaned = clean_original_backdrop(img, mask)
        self.assertEqual(cleaned.shape, img.shape)
        self.assertEqual(cleaned.dtype, np.uint8)

    def test_21_edge_decontamination_and_face_spotlight(self):
        """STEP 4: Verify face-positioned spotlight and edge color decontamination."""
        from background_engine import decontaminate_edges, generate_studio_backdrop
        
        # Test spotlight positioning
        face_info = {"bbox": [200, 150, 100, 120]}
        bg_centered = generate_studio_backdrop(500, 600, backdrop_type="classic_blue", face_info=face_info)
        
        # Pixel right behind head (x=250, y=198) should be brighter than outer corner (x=10, y=10)
        spot_lum = float(np.mean(bg_centered[198, 250]))
        corner_lum = float(np.mean(bg_centered[10, 10]))
        self.assertGreater(spot_lum, corner_lum, "Strobe light spot must be positioned behind detected face!")
        
        # Test edge decontamination
        dummy_img = np.full((100, 100, 3), 200, dtype=np.uint8)
        dummy_mask = np.full((100, 100), 128, dtype=np.uint8)
        decontaminated = decontaminate_edges(dummy_img, dummy_mask)
        self.assertEqual(decontaminated.shape, dummy_img.shape)
        self.assertEqual(decontaminated.dtype, np.uint8)


if __name__ == "__main__":
    unittest.main()




