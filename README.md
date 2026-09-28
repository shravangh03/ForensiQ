# ForensiQ — Digital Forensics & Data Sanitization Platform 🛡️🔬

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Theme: Slate & Zinc Enterprise Dark](https://img.shields.io/badge/theme-Slate%20%26%20Zinc%20Dark-0f172a.svg)]()

**ForensiQ** is an enterprise-grade, browser-accessible **Digital Forensics Workstation & Data Sanitization Platform** built for SIH26149. It enables investigators to perform read-only disk carving, SHA-256 chain-of-custody verification, automated artifact classification, AI-assisted case analysis, and standards-compliant secure data erasure simulations.

---

## 🌟 Key Features

### 🔍 Read-Only Forensic Carving Engine
- **Hardware Write-Block Protection**: All disk media analysis runs in strict read-only mode to prevent evidence tampering.
- **Magic Number Signature Detection**: Automatically carves files across raw disk sectors (`.raw`, `.dd`, `.img`) for JPEGs, PNGs, PDFs, and TXT logs.
- **Rule-Based Confidence Scoring**: Evaluates file headers, footers, entropy, and structural integrity to assign a confidence index (0–100%).

### 📜 Chain of Custody & Cryptographic Hashing
- **SHA-256 Digest Engine**: Computes streaming integrity hashes for all evidence disk images and carved artifacts.
- **Immutable Audit Vault**: Records every investigator action, scan start, artifact extraction, and report generation step with UTC timestamps.

### 🤖 AI Forensic Assistant (Zero-Hallucination Guard)
- **Deterministic Q&A**: Answers investigator queries strictly based on confirmed database evidence (e.g., file counts, confidence scores, SHA-256 hashes, timelines).
- **Interactive Quick Prompts**: Instant case summarization, PDF listing, and timeline creation.

### 🛡️ Secure Data Erasure Simulator
- **Standards-Compliant Sanitization**: Demonstrates DoD 5220.22-M (3-Pass), IEEE 2883-2022 Purge, NIST SP 800-88 Rev. 2, and Gutmann 35-Pass erasure protocols.
- **Post-Erase Verification**: Simulates 100% sector read-back and zero-hash block validation.

### 🎨 Enterprise Theme System & Mobile Responsiveness
- **5 Dynamic Themes**:
  - 🌌 *Slate & Zinc Enterprise Dark* (Default)
  - ⚡ *Cyber Midnight*
  - 🟢 *Emerald Matrix*
  - 🔴 *Obsidian Crimson*
  - ☀️ *Zinc Enterprise Light*
- **100% Mobile Responsive**: Includes a slide-out navigation drawer, fluid grids, and touch-optimized responsive data tables across desktop, tablet, and mobile viewports.

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.8+ installed on Windows, macOS, or Linux.

### 1. Clone the Repository
```bash
git clone https://github.com/shravangh03/ForensiQ.git
cd ForensiQ
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Application
```bash
python app.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 📁 Project Architecture

```
ForensiQ/
├── app.py                      # Core Flask web server & route handlers
├── database.py                 # SQLite schema & database connection layer
├── requirements.txt            # Python dependencies
├── README.md                   # Platform documentation
├── .gitignore                  # Git ignore rules
│
├── forensic/                   # Forensics carving & hashing engine
│   ├── analyzer.py             # Disk sector reader & carver
│   ├── classifier.py           # Artifact confidence scorer & statistics
│   ├── hashing.py              # SHA-256 streaming hashing module
│   └── signatures.py           # Magic number headers/footers registry
│
├── audit/                      # Audit logging module
│   └── audit_logger.py         # Chain-of-custody audit trail manager
│
├── ai/                         # Deterministic AI assistant
│   └── assistant.py            # Case Q&A database query engine
│
├── reports/                    # Report generation engine
│   └── report_generator.py     # HTML court-admissible report compiler
│
├── demo/                       # Demo evidence generator
│   └── generate_demo_evidence.py # Creates synthetic raw drive images for testing
│
├── static/                     # Frontend static assets
│   ├── css/
│   │   └── style.css           # Custom CSS variables, themes & responsive breakpoints
│   └── js/
│       └── main.js             # Client JS, theme switcher & mobile drawer
│
└── templates/                  # Jinja2 HTML View Templates
    ├── base.html               # Main layout, sidebar drawer & header bar
    ├── dashboard.html          # Overview dashboard & KPI cards
    ├── case.html               # Case & evidence image manager
    ├── recovery.html           # Live recovery scan studio
    ├── artifacts.html          # Carved artifact explorer & hex viewer
    ├── audit.html              # Immutable chain-of-custody audit log
    ├── reports.html            # Forensic investigation report builder
    ├── sanitization.html       # Data erasure simulator
    └── ai_assistant.html       # AI case query interface
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.

---
*Developed for SIH26149 — ForensiQ Workstation*
