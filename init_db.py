"""
KameraPh Database Schema Instantiation & Initialization Engine
Supports both SQLite (Local Zero-Config Development) & PostgreSQL (Supabase / Production).
"""

import os
import sqlite3
import uuid
import hashlib
import datetime
from typing import Optional, Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "kameraph.db")
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")


def get_db_connection():
    """Returns a SQLite database connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Computes SHA-256 hash with salt for secure credential storage."""
    salt = os.environ.get("JWT_SECRET", "kameraph_salt_2026")
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()


def init_database():
    """Instantiates the database schema and populates initial default records."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Studios Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS studios (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        studio_name TEXT NOT NULL,
        owner_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone_number TEXT,
        location_city TEXT DEFAULT 'Manila',
        credit_balance INTEGER DEFAULT 150 NOT NULL,
        plan_tier TEXT DEFAULT 'studio_pro',
        gcash_account_number TEXT
    );
    """)

    # 2. Users / Auth Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'studio_user', -- 'super_admin' | 'studio_admin' | 'studio_user'
        studio_id TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE SET NULL
    );
    """)

    # 3. Batches Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS batches (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        studio_id TEXT NOT NULL,
        school_name TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        grade_level TEXT,
        section_name TEXT,
        regalia_type TEXT DEFAULT 'standard_toga',
        total_photos INTEGER DEFAULT 0,
        status TEXT DEFAULT 'in_progress',
        FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE CASCADE
    );
    """)

    # 4. Photos Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS photos (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        batch_id TEXT,
        studio_id TEXT NOT NULL,
        student_name TEXT,
        student_id_number TEXT,
        filename TEXT NOT NULL,
        original_r2_url TEXT NOT NULL,
        enhanced_r2_url TEXT,
        thumbnail_url TEXT,
        crop_8r_url TEXT,
        crop_2x2_url TEXT,
        toga_iron_strength REAL DEFAULT 0.70,
        skin_smoothing_ratio REAL DEFAULT 0.65,
        shine_reduction REAL DEFAULT 0.35,
        dark_spot_whitening REAL DEFAULT 0.50,
        lip_color TEXT DEFAULT '#d87093',
        lip_intensity REAL DEFAULT 0.35,
        backdrop_type TEXT DEFAULT 'royal_navy',
        bg_replacement_enabled INTEGER DEFAULT 1,
        lighting_temp TEXT DEFAULT 'neutral_5500k',
        studio_light_intensity REAL DEFAULT 0.20,
        processing_latency_ms INTEGER DEFAULT 0,
        gpu_engine_used TEXT DEFAULT 'local_cpu',
        review_needed INTEGER DEFAULT 0,
        review_reason TEXT,
        status TEXT DEFAULT 'completed',
        FOREIGN KEY (batch_id) REFERENCES batches(id) ON DELETE CASCADE,
        FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE CASCADE
    );
    """)

    # 5. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        studio_id TEXT NOT NULL,
        paymongo_session_id TEXT UNIQUE NOT NULL,
        payment_method TEXT NOT NULL,
        package_id TEXT NOT NULL,
        amount_php REAL NOT NULL,
        credits_added INTEGER NOT NULL,
        payment_status TEXT DEFAULT 'paid',
        receipt_url TEXT,
        FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE CASCADE
    );
    """)

    # 6. Export Jobs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS export_jobs (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        studio_id TEXT NOT NULL,
        batch_id TEXT,
        export_type TEXT NOT NULL,
        school_name TEXT NOT NULL,
        status TEXT DEFAULT 'processing',
        progress_percentage INTEGER DEFAULT 0,
        download_url TEXT,
        error_message TEXT,
        FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE CASCADE
    );
    """)

    conn.commit()

    # Seed initial default studio and admin user if empty
    cursor.execute("SELECT COUNT(*) as count FROM studios;")
    if cursor.fetchone()["count"] == 0:
        studio_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO studios (id, created_at, studio_name, owner_name, email, phone_number, location_city, credit_balance, plan_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (studio_id, now, "AuraGrad Creative Studio (Manila)", "Juan Dela Cruz", "editor@auragrad-studio.ph", "+63 917 123 4567", "Manila", 150, "studio_pro"))

        # Seed super admin and studio editor
        admin_pass_hash = hash_password("KameraPhAdminSecure2026!")
        cursor.execute("""
            INSERT INTO users (id, created_at, email, password_hash, full_name, role, studio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (str(uuid.uuid4()), now, "admin@kameraph.com", admin_pass_hash, "KameraPh System Admin", "super_admin", None))

        user_pass_hash = hash_password("StudioEditor2026!")
        cursor.execute("""
            INSERT INTO users (id, created_at, email, password_hash, full_name, role, studio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (str(uuid.uuid4()), now, "editor@auragrad-studio.ph", user_pass_hash, "Juan Dela Cruz", "studio_admin", studio_id))

        batch_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO batches (id, created_at, studio_id, school_name, academic_year, grade_level, section_name, regalia_type, total_photos, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (batch_id, now, studio_id, "Manila Science High School", "2025-2026", "Senior High School (Grade 12)", "STEM-12A", "standard_toga", 1, "in_progress"))

        txn_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO transactions (id, created_at, studio_id, paymongo_session_id, payment_method, package_id, amount_php, credits_added, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (txn_id, now, studio_id, f"cs_init_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}", "gcash", "school_500", 1850.00, 500, "paid"))

        conn.commit()
        print(f"Database schema instantiated and seeded at {DB_PATH}")

    conn.close()
    return DB_PATH


if __name__ == "__main__":
    init_database()
