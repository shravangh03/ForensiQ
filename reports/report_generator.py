import os
from database import get_db_connection
from audit.audit_logger import get_audit_logs

def generate_forensic_html_report(case_id):
    """
    Generates a formal, professional HTML Forensic Investigation Report for a specified case.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch Case Info
    cursor.execute("SELECT * FROM cases WHERE case_id = ?", (case_id,))
    case_row = cursor.fetchone()
    if not case_row:
        conn.close()
        return None

    case = dict(case_row)

    # Fetch Evidence Info
    cursor.execute("SELECT * FROM evidence WHERE case_id = ?", (case_id,))
    evidence_rows = cursor.fetchall()
    evidence_list = [dict(row) for row in evidence_rows]

    # Fetch Artifacts Info
    cursor.execute("SELECT * FROM artifacts WHERE case_id = ? ORDER BY offset ASC", (case_id,))
    artifact_rows = cursor.fetchall()
    artifacts_list = [dict(row) for row in artifact_rows]

    conn.close()

    # Fetch Audit Logs
    audit_logs = get_audit_logs(case_id=case_id, limit=500)

    # Classification stats
    stats = {}
    high_conf = 0
    for art in artifacts_list:
        ftype = art['file_type']
        stats[ftype] = stats.get(ftype, 0) + 1
        if art['confidence'] >= 75:
            high_conf += 1

    # Generate HTML content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Forensic Report — {case['case_id']}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #0f172a;
            color: #e2e8f0;
            margin: 0;
            padding: 40px;
            line-height: 1.6;
        }}
        .report-card {{
            max-width: 1000px;
            margin: 0 auto;
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 40px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        .header {{
            border-bottom: 2px solid #00f2fe;
            padding-bottom: 20px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{
            margin: 0;
            color: #00f2fe;
            font-size: 26px;
            letter-spacing: 1px;
        }}
        .badge-demo {{
            background-color: #ef4444;
            color: #ffffff;
            font-weight: bold;
            padding: 6px 14px;
            border-radius: 4px;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .section-title {{
            color: #38bdf8;
            font-size: 18px;
            border-bottom: 1px solid #334155;
            padding-bottom: 8px;
            margin-top: 30px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .meta-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }}
        .meta-item {{
            background: #0f172a;
            padding: 12px 18px;
            border-radius: 6px;
            border-left: 3px solid #00f2fe;
        }}
        .meta-label {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
        }}
        .meta-value {{
            font-size: 15px;
            font-weight: 600;
            color: #f8fafc;
            word-break: break-all;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 13px;
        }}
        th, td {{
            padding: 10px 12px;
            text-align: left;
            border-bottom: 1px solid #334155;
        }}
        th {{
            background-color: #0f172a;
            color: #38bdf8;
            text-transform: uppercase;
            font-size: 11px;
        }}
        tr:nth-child(even) {{
            background-color: #162032;
        }}
        .status-valid {{
            color: #4ade80;
            font-weight: bold;
        }}
        .status-partial {{
            color: #facc15;
            font-weight: bold;
        }}
        .status-corrupt {{
            color: #f87171;
            font-weight: bold;
        }}
        .disclaimer {{
            margin-top: 40px;
            padding: 15px;
            background-color: #451a03;
            border: 1px solid #78350f;
            border-radius: 6px;
            color: #fde68a;
            font-size: 13px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="report-card">
        <div class="header">
            <div>
                <h1>DIGITAL FORENSICS INVESTIGATION REPORT</h1>
                <div style="font-size: 13px; color: #94a3b8; margin-top: 4px;">ForensiQ Platform Prototype (SIH26149)</div>
            </div>
            <span class="badge-demo">PROTOTYPE DEMO REPORT</span>
        </div>

        <div class="section-title">1. Case Metadata</div>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Case Identifier</div>
                <div class="meta-value">{case['case_id']}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Lead Investigator</div>
                <div class="meta-value">{case['investigator']}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Creation Timestamp</div>
                <div class="meta-value">{case['created_at']}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Case Description</div>
                <div class="meta-value">{case['description'] or 'N/A'}</div>
            </div>
        </div>

        <div class="section-title">2. Evidence Media Summary</div>
    """

    for ev in evidence_list:
        html_content += f"""
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Evidence Image Name</div>
                <div class="meta-value">{ev['filename']}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">File Size</div>
                <div class="meta-value">{ev['size']:,} bytes</div>
            </div>
            <div class="meta-item" style="grid-column: span 2;">
                <div class="meta-label">SHA-256 Evidence Hash (Read-Only Verification)</div>
                <div class="meta-value" style="font-family: monospace; color: #00f2fe;">{ev['sha256'] or 'CALCULATING...'}</div>
            </div>
        </div>
        """

    html_content += f"""
        <div class="section-title">3. Recovery Statistics</div>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Total Artifacts Carved</div>
                <div class="meta-value">{len(artifacts_list)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">High Confidence (&ge;75%)</div>
                <div class="meta-value" style="color: #4ade80;">{high_conf}</div>
            </div>
            <div class="meta-item" style="grid-column: span 2;">
                <div class="meta-label">Type Distribution</div>
                <div class="meta-value">{", ".join([f"{k}: {v}" for k,v in stats.items()]) or "None"}</div>
            </div>
        </div>

        <div class="section-title">4. Recovered Artifact Manifest</div>
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Filename</th>
                    <th>Type</th>
                    <th>Offset</th>
                    <th>Size</th>
                    <th>Confidence</th>
                    <th>Status</th>
                    <th>SHA-256 Hash</th>
                </tr>
            </thead>
            <tbody>
    """

    for art in artifacts_list:
        status_cls = "status-valid" if art['confidence'] >= 75 else ("status-partial" if art['confidence'] >= 50 else "status-corrupt")
        html_content += f"""
            <tr>
                <td>#{art['id']}</td>
                <td><strong>{art['filename']}</strong></td>
                <td>{art['file_type']}</td>
                <td>0x{art['offset']:X}</td>
                <td>{art['size']:,} B</td>
                <td><strong>{art['confidence']}%</strong></td>
                <td class="{status_cls}">{art['validation_status']}</td>
                <td style="font-family: monospace; font-size: 11px;">{art['sha256'][:16]}...</td>
            </tr>
        """

    html_content += f"""
            </tbody>
        </table>

        <div class="section-title">5. Chain of Custody Audit Log</div>
        <table>
            <thead>
                <tr>
                    <th>Timestamp</th>
                    <th>Operation</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
    """

    for log in reversed(audit_logs):
        html_content += f"""
            <tr>
                <td style="font-size: 11px; color: #94a3b8;">{log['timestamp']}</td>
                <td><span style="color: #00f2fe; font-weight: 600;">{log['operation']}</span></td>
                <td>{log['description']}</td>
            </tr>
        """

    html_content += """
            </tbody>
        </table>

        <div class="disclaimer">
            <strong>NOTICE:</strong> This document was generated automatically by the ForensiQ Digital Forensics Workstation (SIH26149). All disk image operations were executed in READ-ONLY mode.
        </div>
    </div>
</body>
</html>
    """

    # Save report HTML to case directory
    report_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cases', case_id, 'reports')
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"Forensic_Report_{case_id}.html")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return report_path
