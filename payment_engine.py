"""
KameraPh Monetization & Asynchronous Payment Engine
---------------------------------------------------
Handles:
  - PayMongo Checkout Sessions (GCash, Maya, Cards, GrabPay)
  - Cryptographically signed webhook verification (HMAC SHA-256)
  - Idempotent credit top-up strictly upon verified payment callbacks
  - Multi-tenant studio transaction ledger
"""

import os
import time
import hmac
import hashlib
import json
import sqlite3
import requests
from typing import Optional, Dict, Any

from init_db import get_db_connection


class PayMongoEngine:
    def __init__(self):
        self.secret_key = os.environ.get("PAYMONGO_SECRET_KEY", "prv_test_mock_key")
        self.public_key = os.environ.get("PAYMONGO_PUBLIC_KEY", "pub_test_mock_key")
        self.webhook_secret = os.environ.get("PAYMONGO_WEBHOOK_SECRET", "")
        self.is_live = not self.secret_key.startswith("prv_test")
        self.api_base = "https://api.paymongo.com/v1"

    # Pre-defined packages calibrated for Philippine graduation studio contract margins
    PACKAGES = {
        "starter_100": {
            "id": "starter_100",
            "name": "Starter Batch (100 Photos)",
            "credits": 100,
            "price_php": 450.00,
            "cost_per_photo": 4.50,
            "description": "Ideal for small school sections or preschool grad pictorials"
        },
        "school_500": {
            "id": "school_500",
            "name": "School Batch Pro (500 Photos)",
            "credits": 500,
            "price_php": 1850.00,
            "cost_per_photo": 3.70,
            "description": "Most Popular: Perfect for Senior High or College batches",
            "popular": True
        },
        "volume_2500": {
            "id": "volume_2500",
            "name": "Studio Enterprise (2,500 Photos)",
            "credits": 2500,
            "price_php": 7500.00,
            "cost_per_photo": 3.00,
            "description": "Full graduation season contract license with priority GPU queue"
        }
    }

    def create_checkout_session(
        self,
        package_id: str,
        studio_id: str,
        studio_email: str,
        studio_name: str,
        success_url: str = "http://127.0.0.1:8000/?payment=success",
        cancel_url: str = "http://127.0.0.1:8000/?payment=cancelled"
    ) -> Dict[str, Any]:
        """Creates a PayMongo Checkout Session for GCash, Maya, and Card payment."""
        package = self.PACKAGES.get(package_id)
        if not package:
            return {"error": "Invalid package_id selected"}

        amount_in_cents = int(package["price_php"] * 100)

        # In local/test mode without live credentials, generate verified simulated session
        if self.secret_key.startswith("prv_test") or not self.is_live:
            session_id = f"cs_test_{int(time.time()*1000)}"
            mock_checkout_url = f"/api/payments/checkout-mock?session_id={session_id}&pkg={package_id}&amount={package['price_php']}"
            
            # Record pending transaction in DB
            self._record_pending_transaction(session_id, studio_id, package_id, package["price_php"], package["credits"])
            
            return {
                "checkout_url": mock_checkout_url,
                "session_id": session_id,
                "package": package,
                "mode": "test_simulation",
                "payment_methods": ["gcash", "paymaya", "card", "grab_pay"]
            }

        # Live PayMongo API Request
        payload = {
            "data": {
                "attributes": {
                    "billing": {
                        "name": studio_name,
                        "email": studio_email
                    },
                    "send_email_receipt": True,
                    "show_description": True,
                    "show_line_items": True,
                    "payment_method_types": ["gcash", "paymaya", "card", "grab_pay"],
                    "line_items": [
                        {
                            "currency": "PHP",
                            "amount": amount_in_cents,
                            "description": package["description"],
                            "name": f"KameraPh {package['name']}",
                            "quantity": 1
                        }
                    ],
                    "success_url": success_url,
                    "cancel_url": cancel_url
                }
            }
        }

        try:
            response = requests.post(
                f"{self.api_base}/checkout_sessions",
                json=payload,
                auth=(self.secret_key, ""),
                headers={"Content-Type": "application/json"}
            )
            data = response.json()
            checkout_url = data["data"]["attributes"]["checkout_url"]
            session_id = data["data"]["id"]
            
            self._record_pending_transaction(session_id, studio_id, package_id, package["price_php"], package["credits"])
            
            return {
                "checkout_url": checkout_url,
                "session_id": session_id,
                "package": package,
                "mode": "live"
            }
        except Exception as e:
            return {"error": str(e)}

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """
        Validates HMAC SHA256 signature from PayMongo webhooks to prevent spoofing.
        Header format: t=timestamp,te=test_signature,li=live_signature
        """
        if not signature_header:
            return False
            
        secret = self.webhook_secret or os.environ.get("PAYMONGO_WEBHOOK_SECRET", "")
        if not secret:
            return False
            
        try:
            parts = dict(x.split("=", 1) for x in signature_header.split(",") if "=" in x)
            timestamp = parts.get("t", "")
            signature = parts.get("li") or parts.get("te")
            if not signature or not timestamp:
                return False
                
            signed_payload = f"{timestamp}.{raw_body.decode('utf-8')}"
            expected_sig = hmac.new(
                secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected_sig, signature)
        except Exception:
            return False

    def handle_webhook_event(self, event_data: dict) -> Dict[str, Any]:
        """
        Processes asynchronous payment webhooks idempotently:
          1. Verifies transaction was previously pending.
          2. Prevents double-crediting via idempotency checks.
          3. Credits the specific studio account.
        """
        data = event_data.get("data", {})
        attributes = data.get("attributes", {})
        event_type = attributes.get("type") or event_data.get("type", "")
        
        # Only process paid events
        if event_type not in ["checkout_session.payment.paid", "payment.paid"]:
            return {"success": False, "message": f"Ignored non-payment event: {event_type}"}

        event_resource = attributes.get("data", {})
        resource_attrs = event_resource.get("attributes", {})
        
        session_id = event_resource.get("id") or event_data.get("session_id")
        payment_method = resource_attrs.get("payment_method_used", "gcash")
        
        if not session_id:
            return {"success": False, "error": "Missing checkout session identifier"}

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check transaction in database
        cursor.execute("SELECT * FROM transactions WHERE paymongo_session_id = ?", (session_id,))
        txn = cursor.fetchone()
        
        if not txn:
            conn.close()
            return {"success": False, "error": "No matching pending checkout session found"}

        # Idempotency check: if already marked paid, do not re-add credits!
        if txn["payment_status"] == "paid":
            conn.close()
            return {
                "success": True,
                "message": "Transaction already processed",
                "session_id": session_id,
                "credits_added": 0
            }

        credits_to_add = txn["credits_added"]
        studio_id = txn["studio_id"]

        # Mark paid
        cursor.execute("""
            UPDATE transactions 
            SET payment_status = 'paid', payment_method = ? 
            WHERE paymongo_session_id = ?;
        """, (payment_method, session_id))

        # Credit specific studio balance atomically
        cursor.execute("UPDATE studios SET credit_balance = credit_balance + ? WHERE id = ?;", (credits_to_add, studio_id))
        
        # Fetch updated studio balance
        cursor.execute("SELECT credit_balance FROM studios WHERE id = ?;", (studio_id,))
        updated_studio = cursor.fetchone()
        new_balance = updated_studio["credit_balance"] if updated_studio else 0
        
        conn.commit()
        conn.close()

        return {
            "success": True,
            "session_id": session_id,
            "event_type": event_type,
            "credits_added": credits_to_add,
            "new_balance": new_balance,
            "watermark_removed": True,
            "gang_sheet_ready": True
        }

    def _record_pending_transaction(self, session_id: str, studio_id: str, package_id: str, amount_php: float, credits: int):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO transactions (id, created_at, studio_id, paymongo_session_id, payment_method, package_id, amount_php, credits_added, payment_status)
                VALUES (?, datetime('now'), ?, ?, 'pending', ?, ?, ?, 'pending');
            """, (f"txn_{int(time.time()*1000)}", studio_id, session_id, package_id, amount_php, credits))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Notice recording pending transaction:", e)


payment_engine = PayMongoEngine()
