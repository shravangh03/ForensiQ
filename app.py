import os
import json
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory,
    redirect,
    url_for,
)
from database import init_db, get_db_connection
from audit.audit_logger import log_audit_event, get_audit_logs
from forensic.hashing import calculate_sha256
from forensic.analyzer import analyze_evidence_image
from forensic.classifier import classify_artifacts
from reports.report_generator import generate_forensic_html_report
from ai.assistant import ForensicAIAssistant
from demo.generate_demo_evidence import generate_demo_disk_image, DEMO_IMAGE_PATH

app = Flask(__name__)
app.secret_key = "sih2026_forensic_secret_key"

# Initialize database on startup
init_db()


# Create default demo case if none exists
def seed_demo_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM cases")
    count = cursor.fetchone()[0]

    if count == 0:
        print("[SEED] Creating initial default demo case CASE-2026-001...")
        cursor.execute(
            """
            INSERT INTO cases (case_id, investigator, description)
            VALUES ('CASE-2026-001', 'Demo Investigator', 'Digital evidence recovery test on synthetic raw drive image.')
        """
        )
        conn.commit()

        # Ensure demo evidence image file exists
        if not os.path.exists(DEMO_IMAGE_PATH):
            generate_demo_disk_image()

        file_size = os.path.getsize(DEMO_IMAGE_PATH)
        sha256_hash = calculate_sha256(DEMO_IMAGE_PATH)

        cursor.execute(
            """
            INSERT INTO evidence (case_id, filename, file_path, size, sha256)
            VALUES ('CASE-2026-001', 'demo_evidence.raw', ?, ?, ?)
        """,
            (DEMO_IMAGE_PATH, file_size, sha256_hash),
        )
        evidence_id = cursor.lastrowid
        conn.commit()

        log_audit_event(
            "CASE_CREATED",
            "Initial Case CASE-2026-001 created automatically.",
            case_id="CASE-2026-001",
        )
        log_audit_event(
            "EVIDENCE_IMPORTED",
            "Synthetic disk image demo_evidence.raw imported.",
            case_id="CASE-2026-001",
        )
        log_audit_event(
            "HASH_CALCULATED",
            f"SHA-256 evidence integrity hash computed: {sha256_hash}",
            case_id="CASE-2026-001",
        )

    conn.close()


seed_demo_data()

# ----------------------------------------------------
# ROUTES & VIEWS
# ----------------------------------------------------


@app.route("/")
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM cases")
    total_cases = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM evidence")
    total_evidence = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM artifacts")
    total_artifacts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM artifacts WHERE confidence >= 75")
    high_conf_count = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM cases ORDER BY id DESC LIMIT 5")
    recent_cases = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        total_cases=total_cases,
        total_evidence=total_evidence,
        total_artifacts=total_artifacts,
        high_conf_count=high_conf_count,
        recent_cases=recent_cases,
    )


@app.route("/cases")
def cases_view():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]

    evidence_by_case = {}
    for c in cases:
        cursor.execute("SELECT * FROM evidence WHERE case_id = ?", (c["case_id"],))
        evidence_by_case[c["case_id"]] = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "case.html", active_page="cases", cases=cases, evidence_by_case=evidence_by_case
    )


@app.route("/cases/create", methods=["POST"])
def create_case():
    case_id = request.form.get("case_id", "").strip()
    investigator = request.form.get("investigator", "").strip()
    description = request.form.get("description", "").strip()

    if not case_id or not investigator:
        return redirect(url_for("cases_view"))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO cases (case_id, investigator, description)
            VALUES (?, ?, ?)
        """,
            (case_id, investigator, description),
        )
        conn.commit()
        log_audit_event(
            "CASE_CREATED",
            f"New case created by {investigator}: {description}",
            case_id=case_id,
        )
    except Exception as e:
        print("Error creating case:", e)
    finally:
        conn.close()

    return redirect(url_for("cases_view"))


@app.route("/evidence/import", methods=["POST"])
def import_evidence():
    case_id = request.form.get("case_id")
    use_demo = request.form.get("use_demo_image") == "true"

    if not case_id:
        return redirect(url_for("cases_view"))

    target_path = None
    filename = None

    if use_demo:
        if not os.path.exists(DEMO_IMAGE_PATH):
            generate_demo_disk_image()
        target_path = DEMO_IMAGE_PATH
        filename = "demo_evidence.raw"
    else:
        file = request.files.get("evidence_file")
        if file and file.filename:
            upload_dir = os.path.join(
                os.path.dirname(__file__), "cases", case_id, "evidence"
            )
            os.makedirs(upload_dir, exist_ok=True)
            target_path = os.path.join(upload_dir, file.filename)
            file.save(target_path)
            filename = file.filename

    if target_path and os.path.exists(target_path):
        file_size = os.path.getsize(target_path)
        log_audit_event(
            "EVIDENCE_IMPORTED",
            f"Imported raw disk image: {filename} ({file_size:,} bytes)",
            case_id=case_id,
        )

        # Compute SHA-256 Hash
        sha256_hash = calculate_sha256(target_path)
        log_audit_event(
            "HASH_CALCULATED",
            f"Read-only streaming SHA-256 hash calculated: {sha256_hash}",
            case_id=case_id,
        )

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO evidence (case_id, filename, file_path, size, sha256)
            VALUES (?, ?, ?, ?, ?)
        """,
            (case_id, filename, target_path, file_size, sha256_hash),
        )
        conn.commit()
        conn.close()

    return redirect(url_for("recovery_studio", case_id=case_id))


@app.route("/recovery")
def recovery_studio():
    case_id = request.args.get("case_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]

    selected_case = None
    if case_id:
        cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
        row = cursor.fetchone()
        if row:
            selected_case = dict(row)

    if not selected_case and cases:
        selected_case = cases[0]

    evidence_list = []
    artifacts = []
    if selected_case:
        cursor.execute(
            "SELECT * FROM evidence WHERE case_id = ?", (selected_case["case_id"],)
        )
        evidence_list = [dict(r) for r in cursor.fetchall()]

        cursor.execute(
            "SELECT * FROM artifacts WHERE case_id = ? ORDER BY offset ASC",
            (selected_case["case_id"],),
        )
        artifacts = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return render_template(
        "recovery.html",
        active_page="recovery",
        cases=cases,
        selected_case=selected_case,
        evidence_list=evidence_list,
        artifacts=artifacts,
    )


@app.route("/api/recovery/scan", methods=["POST"])
def api_recovery_scan():
    data = request.get_json()
    case_id = data.get("case_id")
    evidence_id = data.get("evidence_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,))
    ev_row = cursor.fetchone()
    conn.close()

    if not ev_row:
        return jsonify({"status": "error", "message": "Evidence image not found."}), 404

    ev = dict(ev_row)
    image_path = ev["file_path"]

    if not os.path.exists(image_path):
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Image file not found at path: {image_path}",
                }
            ),
            400,
        )

    recovered = analyze_evidence_image(case_id, evidence_id, image_path)

    return jsonify(
        {"status": "success", "artifacts_count": len(recovered), "artifacts": recovered}
    )


@app.route("/artifacts")
def artifacts_view():
    case_id = request.args.get("case_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]

    if case_id:
        cursor.execute(
            "SELECT * FROM artifacts WHERE case_id = ? ORDER BY offset ASC", (case_id,)
        )
    else:
        cursor.execute("SELECT * FROM artifacts ORDER BY id DESC")

    artifacts = [dict(r) for r in cursor.fetchall()]
    conn.close()

    classification = classify_artifacts(artifacts)

    return render_template(
        "artifacts.html",
        active_page="artifacts",
        cases=cases,
        selected_case_id=case_id,
        artifacts=artifacts,
        total_count=classification["total"],
        counts=classification["by_type"],
    )


@app.route("/api/artifacts/<int:artifact_id>")
def api_artifact_detail(artifact_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Artifact not found"}), 404

    return jsonify(dict(row))


@app.route("/api/artifacts/<int:artifact_id>/hex")
def api_artifact_hex(artifact_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Artifact not found"}), 404

    art = dict(row)
    file_path = art["file_path"]

    if not os.path.exists(file_path):
        return jsonify({"hex_dump": "File not found on disk."})

    with open(file_path, "rb") as f:
        bytes_data = f.read(128)  # First 128 bytes

    # Format into standard hex + ASCII representation
    lines = []
    for i in range(0, len(bytes_data), 16):
        chunk = bytes_data[i : i + 16]
        hex_str = " ".join(f"{b:02X}" for b in chunk).ljust(48)
        ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{i:08X}  {hex_str}  |{ascii_str}|")

    return jsonify({"hex_dump": "\n".join(lines)})


@app.route("/cases/<case_id>/recovered/<filename>")
def serve_recovered_file(case_id, filename):
    recovered_dir = os.path.join(
        os.path.dirname(__file__), "cases", case_id, "recovered"
    )
    return send_from_directory(recovered_dir, filename)


@app.route("/audit")
def audit_view():
    case_id = request.args.get("case_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    logs = get_audit_logs(case_id=case_id, limit=200)

    return render_template(
        "audit.html",
        active_page="audit",
        cases=cases,
        selected_case_id=case_id,
        audit_logs=logs,
    )


@app.route("/reports")
def reports_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template("reports.html", active_page="reports", cases=cases)


@app.route("/api/reports/generate", methods=["POST"])
def api_generate_report():
    case_id = request.args.get("case_id")
    if not case_id:
        return jsonify({"status": "error", "message": "Missing case_id"}), 400

    report_path = generate_forensic_html_report(case_id)
    if report_path:
        log_audit_event(
            "REPORT_GENERATED",
            f"Generated forensic investigation report: {os.path.basename(report_path)}",
            case_id=case_id,
        )
        return jsonify({"status": "success", "report_path": report_path})
    else:
        return jsonify({"status": "error", "message": "Failed to generate report"}), 500


@app.route("/reports/view/<case_id>")
def view_report_html(case_id):
    report_dir = os.path.join(os.path.dirname(__file__), "cases", case_id, "reports")
    filename = f"Forensic_Report_{case_id}.html"
    return send_from_directory(report_dir, filename)


@app.route("/sanitization")
def sanitization_view():
    return render_template("sanitization.html", active_page="sanitization")


@app.route("/ai")
def ai_assistant_view():
    case_id = request.args.get("case_id")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases ORDER BY id DESC")
    cases = [dict(r) for r in cursor.fetchall()]
    conn.close()

    selected_case_id = case_id if case_id else (cases[0]["case_id"] if cases else "")

    return render_template(
        "ai_assistant.html",
        active_page="ai",
        cases=cases,
        selected_case_id=selected_case_id,
    )


@app.route("/api/ai/ask", methods=["POST"])
def api_ai_ask():
    data = request.get_json()
    case_id = data.get("case_id")
    question = data.get("question", "")

    if not case_id or not question:
        return jsonify({"answer": "Please provide a valid question and case ID."}), 400

    assistant = ForensicAIAssistant(case_id)
    answer = assistant.ask(question)

    return jsonify({"answer": answer})


if __name__ == "__main__":
    print("====================================================")
    print("  SIH26149 FORENSIQ WORKSTATION PLATFORM (SAFE MVP) ")
    print("  Server running on http://127.0.0.1:5000           ")
    print("====================================================")
    app.run(host="127.0.0.1", port=5000, debug=False)
