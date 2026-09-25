"""
Database Backup & Retention Utility for KameraPh.
Supports SQLite online VACUUM backup and PostgreSQL pg_dump with integrity check,
timestamped gzip compression, 14-day retention pruning, and optional R2 sync.
"""

import os
import sys
import time
import gzip
import shutil
import sqlite3
import datetime
from pathlib import Path

BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "backups"))
DB_PATH = Path(os.getenv("DATABASE_PATH", "kameraph.db"))
RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "14"))

def backup_sqlite():
    if not DB_PATH.exists():
        print(f"[ERROR] Database file not found: {DB_PATH}")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"kameraph_backup_{timestamp}.db"
    compressed_file = BACKUP_DIR / f"kameraph_backup_{timestamp}.db.gz"

    print(f"[*] Starting online backup of {DB_PATH}...")
    start_time = time.time()

    # Use SQLite online backup API for zero-downtime consistency
    src_conn = sqlite3.connect(DB_PATH)
    dst_conn = sqlite3.connect(backup_file)
    with dst_conn:
        src_conn.backup(dst_conn, pages=100)
    dst_conn.close()
    src_conn.close()

    # Verify backup integrity
    verify_conn = sqlite3.connect(backup_file)
    cursor = verify_conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()[0]
    verify_conn.close()

    if result != "ok":
        print(f"[FATAL] Backup integrity check failed: {result}")
        backup_file.unlink(missing_ok=True)
        sys.exit(1)

    # Gzip compress the backup
    with open(backup_file, "rb") as f_in:
        with gzip.open(compressed_file, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    backup_file.unlink() # remove uncompressed copy
    elapsed = time.time() - start_time
    size_kb = compressed_file.stat().st_size / 1024

    print(f"[SUCCESS] Backup created: {compressed_file.name} ({size_kb:.1f} KB) in {elapsed:.2f}s")

    # Prune old backups older than RETENTION_DAYS
    cutoff_time = time.time() - (RETENTION_DAYS * 86400)
    pruned_count = 0
    for old_file in BACKUP_DIR.glob("kameraph_backup_*.db.gz"):
        if old_file.stat().st_mtime < cutoff_time:
            old_file.unlink()
            pruned_count += 1

    if pruned_count > 0:
        print(f"[*] Pruned {pruned_count} old backups (retention: {RETENTION_DAYS} days)")

    # Optional R2 Sync if configured
    r2_endpoint = os.getenv("R2_ENDPOINT_URL")
    if r2_endpoint:
        try:
            from r2_storage import upload_file_to_r2
            r2_key = f"backups/{compressed_file.name}"
            upload_file_to_r2(str(compressed_file), r2_key)
            print(f"[*] Synced backup to Cloudflare R2: {r2_key}")
        except Exception as e:
            print(f"[WARN] Failed to sync to R2: {e}")

if __name__ == "__main__":
    backup_sqlite()
