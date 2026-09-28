import os
import json
from database import get_db_connection
from audit.audit_logger import log_audit_event, log_audit_events_batch
from .carver import FileCarver
from .validator import validate_artifact
from .confidence import calculate_confidence_score
from .hashing import calculate_bytes_sha256

def analyze_evidence_image(case_id, evidence_id, image_path, progress_callback=None):
    """
    Executes the Read-Only Forensic Analysis Pipeline on the imported evidence disk image.
    Extracts carved candidates, validates file structure, calculates confidence score,
    persists recovered files into case folder, and updates the database & audit logs.
    """
    log_audit_event('ANALYSIS_STARTED', f"Started forensic read-only analysis on evidence image: {os.path.basename(image_path)}", case_id=case_id)

    # Prepare recovery output directory
    case_recovered_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cases', case_id, 'recovered')
    os.makedirs(case_recovered_dir, exist_ok=True)

    carver = FileCarver(image_path)
    candidates = carver.scan_and_extract(progress_callback=progress_callback)

    recovered_artifacts = []
    audit_events_to_log = []

    conn = get_db_connection()
    cursor = conn.cursor()

    for idx, cand in enumerate(candidates, start=1):
        raw_bytes = cand['raw_bytes']
        file_type = cand['file_type']
        ext = cand['extension']
        offset = cand['offset']
        size = cand['size']

        artifact_filename = f"artifact_{idx:03d}{ext}"
        artifact_path = os.path.join(case_recovered_dir, artifact_filename)

        # Write recovered artifact bytes to case recovery folder
        with open(artifact_path, 'wb') as out_f:
            out_f.write(raw_bytes)

        # Validate artifact
        val_res = validate_artifact(file_type, raw_bytes)

        # Compute confidence score
        confidence, score_breakdown = calculate_confidence_score(val_res)
        validation_status = "VALID" if confidence >= 75 else ("PARTIAL" if confidence >= 50 else "CORRUPT")
        
        details_str = json.dumps({
            'report': val_res['details'],
            'score_breakdown': score_breakdown
        })

        # Calculate artifact SHA-256
        art_sha256 = calculate_bytes_sha256(raw_bytes)

        # Insert into Database
        cursor.execute('''
            INSERT INTO artifacts 
            (case_id, evidence_id, filename, file_path, file_type, offset, size, confidence, validation_status, validation_details, sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (case_id, evidence_id, artifact_filename, artifact_path, file_type, offset, size, confidence, validation_status, details_str, art_sha256))

        artifact_id = cursor.lastrowid

        recovered_artifacts.append({
            'id': artifact_id,
            'filename': artifact_filename,
            'file_type': file_type,
            'offset': offset,
            'size': size,
            'confidence': confidence,
            'validation_status': validation_status,
            'sha256': art_sha256
        })

        audit_events_to_log.append({
            'case_id': case_id,
            'operation': 'ARTIFACT_RECOVERED',
            'description': f"Carved {file_type} artifact ({artifact_filename}) at offset 0x{offset:X} ({size} bytes) with {confidence}% confidence.",
            'artifact_id': artifact_id
        })

    conn.commit()
    conn.close()

    # Batch log audit events
    audit_events_to_log.append({
        'case_id': case_id,
        'operation': 'ANALYSIS_COMPLETED',
        'description': f"Forensic scan completed. Recovered {len(recovered_artifacts)} total artifacts.",
        'artifact_id': None
    })

    log_audit_events_batch(audit_events_to_log)

    return recovered_artifacts
