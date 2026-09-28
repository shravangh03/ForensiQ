import sqlite3
from database import get_db_connection

class ForensicAIAssistant:
    def __init__(self, case_id):
        self.case_id = case_id

    def ask(self, question):
        """
        Answers investigator queries deterministically based on structured SQLite database state.
        Guarantees zero evidence hallucination.
        """
        q = question.lower().strip()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Fetch case
        cursor.execute("SELECT * FROM cases WHERE case_id = ?", (self.case_id,))
        case_row = cursor.fetchone()
        if not case_row:
            conn.close()
            return f"Case '{self.case_id}' not found in database."

        case = dict(case_row)

        # Fetch evidence
        cursor.execute("SELECT * FROM evidence WHERE case_id = ?", (self.case_id,))
        evidence_list = [dict(r) for r in cursor.fetchall()]

        # Fetch artifacts
        cursor.execute("SELECT * FROM artifacts WHERE case_id = ?", (self.case_id,))
        artifacts_list = [dict(r) for r in cursor.fetchall()]

        # Fetch logs
        cursor.execute("SELECT * FROM audit_logs WHERE case_id = ? ORDER BY id ASC", (self.case_id,))
        logs_list = [dict(r) for r in cursor.fetchall()]

        conn.close()

        # 1. Total Recovered Count
        if any(k in q for k in ["how many files", "how many artifacts", "total recovered", "recovered count"]):
            return f"📊 **Artifact Recovery Count:** A total of **{len(artifacts_list)} artifacts** were carved and extracted from evidence image(s) for Case **{self.case_id}**."

        # 2. High Confidence Count
        elif any(k in q for k in ["high-confidence", "high confidence", "score >= 75"]):
            high_conf = [a for a in artifacts_list if a['confidence'] >= 75]
            return f"✅ **High-Confidence Artifacts:** **{len(high_conf)} out of {len(artifacts_list)} artifacts** achieved a confidence score of 75% or higher (valid headers, footers, structure, and renderability)."

        # 3. Filter by File Type (e.g. PDFs, JPEGs, PNGs, TXTs)
        elif "pdf" in q:
            pdfs = [a for a in artifacts_list if a['file_type'] == 'PDF']
            if not pdfs:
                return f"📄 **PDF Artifacts:** No PDF files were carved in case {self.case_id}."
            lines = [f"• **{p['filename']}** | Offset: `0x{p['offset']:X}` | Size: `{p['size']:,} B` | Confidence: `{p['confidence']}%` | Hash: `{p['sha256'][:16]}...`" for p in pdfs]
            return f"📄 **Recovered PDF Files ({len(pdfs)} total):**\n\n" + "\n".join(lines)

        elif "jpeg" in q or "jpg" in q or "image" in q:
            imgs = [a for a in artifacts_list if a['file_type'] in ['JPEG', 'PNG']]
            lines = [f"• **{i['filename']}** ({i['file_type']}) | Offset: `0x{i['offset']:X}` | Size: `{i['size']:,} B` | Confidence: `{i['confidence']}%`" for i in imgs]
            return f"🖼️ **Recovered Image Artifacts ({len(imgs)} total):**\n\n" + "\n".join(lines)

        # 4. Evidence Hash query
        elif any(k in q for k in ["sha256", "hash", "integrity"]):
            if not evidence_list:
                return "No evidence media uploaded yet for this case."
            hashes = [f"• **{e['filename']}**: `{e['sha256']}` ({e['size']:,} bytes)" for e in evidence_list]
            return "🔒 **Read-Only Evidence SHA-256 Hashes:**\n\n" + "\n".join(hashes)

        # 5. Low confidence / Corrupt files
        elif any(k in q for k in ["low confidence", "corrupt", "damaged"]):
            low = [a for a in artifacts_list if a['confidence'] < 75]
            if not low:
                return f"🌟 **Low Confidence Check:** All {len(artifacts_list)} carved artifacts passed verification with high confidence (≥75%)."
            lines = [f"• **{a['filename']}** ({a['file_type']}) | Score: `{a['confidence']}%` | Status: `{a['validation_status']}`" for a in low]
            return f"⚠️ **Low Confidence / Corrupt Candidates ({len(low)} total):**\n\n" + "\n".join(lines)

        # 6. Timeline query
        elif "timeline" in q or "history" in q:
            if not logs_list:
                return "No audit logs recorded."
            lines = [f"⏱️ **{l['timestamp']}** — `{l['operation']}`: {l['description']}" for l in logs_list]
            return f"📜 **Chronological Investigation Timeline ({self.case_id}):**\n\n" + "\n".join(lines)

        # 7. Default Case Summary
        else:
            by_type = {}
            for a in artifacts_list:
                by_type[a['file_type']] = by_type.get(a['file_type'], 0) + 1
            type_str = ", ".join([f"{k}: {v}" for k,v in by_type.items()]) or "None"

            ev_str = f"Image: `{evidence_list[0]['filename']}` (SHA-256: `{evidence_list[0]['sha256'][:16]}...`)" if evidence_list else "No evidence media."

            return f"""🔍 **Case Summary for {case['case_id']}**:
• **Investigator:** {case['investigator']}
• **Description:** {case['description']}
• **Created At:** {case['created_at']}
• **Evidence:** {ev_str}
• **Recovered Artifacts:** {len(artifacts_list)} total ({type_str})
• **Audit Trail Entries:** {len(logs_list)} logged operations.

*All operations performed in strict READ-ONLY mode.*"""
