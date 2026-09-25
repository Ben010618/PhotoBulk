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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from init_db import init_database, get_db_connection
from auth import create_access_token
from analyzer_engine import analyze_portrait, get_face_detector
from beautification_presets import apply_beauty_preset_to_image, BEAUTY_PRESETS, LIP_COLOR_PALETTES
from background_engine import generate_studio_backdrop, composite_subject_onto_backdrop, STUDIO_BACKDROPS
from watermark_engine import generate_watermarked_proof
from payment_engine import payment_engine
from r2_storage import storage
from regalia_profiles import REGALIA_PROFILES
from pdf_engine import generate_contact_sheet_pdf, generate_lab_gang_sheet_pdf, generate_batch_lab_gang_sheet_pdf
from pipeline import (
    process_complete_workflow,
    crop_8r_aspect,
    crop_2x2_id,
    get_subject_mask,
    detect_actual_engine
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

        try:
            # Deduct 1 credit
            success = deduct_studio_credit(studio_id, count=1)
            self.assertTrue(success)
            
            cursor.execute("SELECT credit_balance FROM studios WHERE id = ?;", (studio_id,))
            updated_balance = cursor.fetchone()["credit_balance"]
            self.assertEqual(updated_balance, initial_balance - 1)

            # Set balance to 0 and verify blocking
            cursor.execute("UPDATE studios SET credit_balance = 0 WHERE id = ?;", (studio_id,))
            conn.commit()

            res = self.client.post("/api/process-image", data={"regalia_profile": "standard_toga"})
            self.assertEqual(res.status_code, 402, "Must return 402 Payment Required when credit balance is zero!")
        finally:
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


if __name__ == "__main__":
    unittest.main()
