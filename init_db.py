"""
KameraPh Database Schema Instantiation & Initialization Engine
Supports both SQLite (Local Zero-Config Development) & PostgreSQL (Supabase / Production).
"""

import os
import sqlite3
import uuid
import hashlib
import hmac
import datetime
import bcrypt
from typing import Optional, Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_db_path() -> str:
    """Resolves database file path, honoring DATABASE_PATH or DATA_DIR environment variables for tests."""
    if "DATABASE_PATH" in os.environ:
        return os.environ["DATABASE_PATH"]
    if "DATA_DIR" in os.environ:
        return os.path.join(os.environ["DATA_DIR"], "kameraph.db")
    return os.path.join(BASE_DIR, "kameraph.db")

DB_PATH = get_db_path()
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")


def get_db_connection():
    """Returns a SQLite database connection with row factory and WAL mode enabled for concurrent reads."""
    target_path = get_db_path()
    conn = sqlite3.connect(target_path)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Computes a secure bcrypt hash for credential storage."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a bcrypt hash, with legacy SHA-256 fallback."""
    try:
        if hashed_password.startswith("$2"):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        salt = os.environ.get("JWT_SECRET", "kameraph_salt_2026")
        legacy_hash = hashlib.sha256((plain_password + salt).encode("utf-8")).hexdigest()
        return hmac.compare_digest(hashed_password, legacy_hash)
    except Exception:
        return False


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

    # 7. Asynchronous Background Jobs Ledger
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        studio_id TEXT NOT NULL,
        project_id TEXT,
        job_type TEXT NOT NULL DEFAULT 'batch_process',
        status TEXT NOT NULL DEFAULT 'queued',
        progress_percentage INTEGER DEFAULT 0,
        total_items INTEGER DEFAULT 0,
        processed_items INTEGER DEFAULT 0,
        result_json TEXT,
        error_message TEXT,
        FOREIGN KEY (studio_id) REFERENCES studios(id) ON DELETE CASCADE
    );
    """)

    # Migration guard: ensure project_id column exists
    cursor.execute("PRAGMA table_info(jobs);")
    job_cols = [col["name"] for col in cursor.fetchall()]
    if "project_id" not in job_cols:
        cursor.execute("ALTER TABLE jobs ADD COLUMN project_id TEXT;")

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

        # Seed super admin and studio editor credentials from environment variables
        is_debug = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
        admin_pass = os.environ.get("ADMIN_SEED_PASSWORD")
        studio_pass = os.environ.get("STUDIO_SEED_PASSWORD")

        if not admin_pass:
            if is_debug:
                admin_pass = "dev_admin_password_123"
            else:
                raise RuntimeError("ADMIN_SEED_PASSWORD must be configured in environment when DEBUG is False")

        if not studio_pass:
            if is_debug:
                studio_pass = "dev_studio_password_123"
            else:
                raise RuntimeError("STUDIO_SEED_PASSWORD must be configured in environment when DEBUG is False")

        admin_pass_hash = hash_password(admin_pass)
        cursor.execute("""
            INSERT INTO users (id, created_at, email, password_hash, full_name, role, studio_id)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (str(uuid.uuid4()), now, "admin@kameraph.com", admin_pass_hash, "KameraPh System Admin", "super_admin", None))

        user_pass_hash = hash_password(studio_pass)
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


def record_job_db(
    job_id: str,
    studio_id: str,
    status: str = "queued",
    total: int = 0,
    job_type: str = "batch_process",
    project_id: Optional[str] = None
) -> None:
    """Inserts or updates an initial job record into SQLite database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            INSERT INTO jobs (id, created_at, updated_at, studio_id, project_id, job_type, status, progress_percentage, total_items, processed_items)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 0)
            ON CONFLICT(id) DO UPDATE SET
                updated_at = excluded.updated_at,
                status = excluded.status,
                project_id = COALESCE(excluded.project_id, jobs.project_id),
                job_type = COALESCE(excluded.job_type, jobs.job_type);
        """, (job_id, now, now, studio_id, project_id, job_type, status, total))
        conn.commit()
        conn.close()
    except Exception as e:
        print("[init_db] Notice recording job in DB:", e)


def update_job_db(
    job_id: str,
    status: str,
    progress: int,
    processed: int,
    result_json: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """Updates job progress, state, and results in database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            UPDATE jobs
            SET updated_at = ?, status = ?, progress_percentage = ?, processed_items = ?, result_json = ?, error_message = ?
            WHERE id = ?;
        """, (now, status, progress, processed, result_json, error, job_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print("[init_db] Notice updating job in DB:", e)


def fetch_job_db(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a job record from database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ? LIMIT 1;", (job_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    except Exception as e:
        print("[init_db] Notice fetching job from DB:", e)
    return None


def recover_interrupted_jobs() -> int:
    """
    Recovers any jobs interrupted by server restart/crash:
    Marks any jobs in SQLite table with status 'running', 'processing', or 'queued'
    as 'failed' with message 'Job interrupted by server restart'.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        cursor.execute("""
            UPDATE jobs
            SET status = 'failed',
                error_message = 'Job interrupted by server restart',
                updated_at = ?
            WHERE status IN ('running', 'processing', 'queued');
        """, (now,))
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count
    except Exception as e:
        print("[init_db] Notice recovering interrupted jobs:", e)
        return 0


if __name__ == "__main__":
    init_database()
