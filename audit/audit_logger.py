import sqlite3
from database import get_db_connection

def log_audit_event(operation, description, case_id=None, artifact_id=None, conn=None):
    """
    Records a forensic audit log event in the database.
    Reuses existing connection if provided, otherwise opens and commits a single connection.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (case_id, operation, description, artifact_id)
            VALUES (?, ?, ?, ?)
        ''', (case_id, operation, description, artifact_id))
        conn.commit()
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Failed to record event '{operation}': {e}")
    finally:
        if should_close:
            conn.close()

def log_audit_events_batch(events_list):
    """
    Records a batch of audit events using a single database connection.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        for ev in events_list:
            cursor.execute('''
                INSERT INTO audit_logs (case_id, operation, description, artifact_id)
                VALUES (?, ?, ?, ?)
            ''', (ev.get('case_id'), ev.get('operation'), ev.get('description'), ev.get('artifact_id')))
        conn.commit()
    except Exception as e:
        print(f"[AUDIT LOG ERROR] Failed to record batch audit events: {e}")
    finally:
        conn.close()

def get_audit_logs(case_id=None, limit=200):
    """
    Retrieves chronological audit events.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    if case_id:
        cursor.execute('''
            SELECT * FROM audit_logs
            WHERE case_id = ?
            ORDER BY id DESC
            LIMIT ?
        ''', (case_id, limit))
    else:
        cursor.execute('''
            SELECT * FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
        ''', (limit,))
    logs = cursor.fetchall()
    conn.close()
    return [dict(log) for log in logs]
