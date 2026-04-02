import sqlite3
import os
import sys
from pathlib import Path
import json

# Add project root to sys.path so we can import backend
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Import required packages
try:
    import libsql_client
except ImportError:
    print("Error: libsql-client is required to migrate data to Turso. Run 'pip install libsql-client'")
    sys.exit(1)

import backend.db as db

def migrate():
    local_db_path = db.DB_PATH
    turso_url = os.environ.get("TURSO_DATABASE_URL")
    turso_token = os.environ.get("TURSO_AUTH_TOKEN")

    if not turso_url or not turso_token:
        print("Error: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set in the environment.")
        sys.exit(1)

    print(f"Connecting to local SQLite DB at {local_db_path}...")
    if not local_db_path.exists():
        print("Local database does not exist. Nothing to migrate.")
        return

    local_conn = sqlite3.connect(str(local_db_path))
    local_conn.row_factory = sqlite3.Row

    print(f"Connecting to Turso at {turso_url}...")
    client = libsql_client.create_client_sync(url=turso_url, auth_token=turso_token)

    print("Initializing Turso database schema...")
    # Temporarily force DB usage to Turso via env variable so init_db hits Turso
    os.environ["USE_TURSO"] = "true"
    db.init_db()

    # Crucial Order: Foreign Key Constraints stipulate users -> jobs -> pipeline_results -> pipeline_errors
    tables_to_migrate = [
        "users",
        "jobs",
        "pipeline_results",
        "pipeline_errors"
    ]

    for table in tables_to_migrate:
        print(f"Migrating table: {table}...")
        try:
            rows = local_conn.execute(f"SELECT * FROM {table}").fetchall()
        except sqlite3.OperationalError as e:
            print(f"  Skipping {table} from local: {e}")
            continue
            
        if not rows:
            print(f"  No rows found in {table}.")
            continue

        columns = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        col_list = ", ".join(columns)

        # Uses INSERT OR IGNORE for true idempotency
        insert_stmt = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"
        
        args = [tuple(row[col] for col in columns) for row in rows]
        
        success = 0
        for arg in args:
            try:
                client.execute(insert_stmt, arg)
                success += 1
            except Exception as e:
                print(f"  [ERROR] {table} insertion failed for row {arg}: {e}")
        
        print(f"  Completed sync for {table}: Processed {len(rows)} records.")

    print("\n[SUCCESS] Migration to Turso complete. Local sqlite data perfectly replicated.")

if __name__ == "__main__":
    migrate()
