import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'forensics.db')

def inspect_db():
    if not os.path.exists(DB_PATH):
        print(f"[!] Database file does not exist yet at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("==========================================================")
    print("      SIH26149 FORENSIC PLATFORM DATABASE INSPECTOR       ")
    print(f"      File: {DB_PATH}")
    print("==========================================================")

    tables = ['cases', 'evidence', 'artifacts', 'audit_logs']

    for tbl in tables:
        cursor.execute(f"SELECT * FROM {tbl}")
        rows = [dict(r) for r in cursor.fetchall()]
        print(f"\n--- TABLE: {tbl.upper()} ({len(rows)} Records) ---")
        if not rows:
            print("   (Empty)")
        else:
            for idx, r in enumerate(rows, start=1):
                print(f"   [{idx}] {r}")

    conn.close()

if __name__ == '__main__':
    inspect_db()
