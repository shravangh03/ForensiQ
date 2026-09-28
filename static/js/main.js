// ForensiQ Workstation Main JavaScript

// Theme Initialization & Switcher
function initTheme() {
    const savedTheme = localStorage.getItem('forensic_theme') || 'slate-zinc';
    document.documentElement.setAttribute('data-theme', savedTheme);
    const themeSelect = document.getElementById('themeSelector');
    if (themeSelect) themeSelect.value = savedTheme;
}

function changeTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('forensic_theme', themeName);
}

// Mobile Sidebar Drawer Controller
function toggleMobileSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (sidebar && backdrop) {
        const isOpen = sidebar.classList.contains('mobile-open');
        if (isOpen) {
            sidebar.classList.remove('mobile-open');
            backdrop.classList.remove('active');
            document.body.style.overflow = '';
        } else {
            sidebar.classList.add('mobile-open');
            backdrop.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
    }
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    if (sidebar && backdrop) {
        sidebar.classList.remove('mobile-open');
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    console.log("[ForensiQ Platform] Workstation UI Initialized.");
    
    // Close mobile menu or modal on Escape key press
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeMobileSidebar();
            closeModal();
        }
    });
});

// 1. Recovery Scan Runner
async function startAnalysis(caseId, evidenceId) {
    const btn = document.getElementById('startScanBtn');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');

    if (!evidenceId) {
        alert("Please select a target evidence image from the dropdown first!");
        return;
    }

    if (btn) btn.disabled = true;
    if (progressText) progressText.innerText = "Initializing Read-Only Disk Stream Reader...";
    if (progressBar) progressBar.style.width = "15%";

    try {
        if (progressBar) progressBar.style.width = "40%";
        if (progressText) progressText.innerText = "Scanning sector magic numbers & headers...";

        const response = await fetch('/api/recovery/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: caseId, evidence_id: parseInt(evidenceId) })
        });

        const data = await response.json();

        if (data.status === 'success') {
            if (progressBar) progressBar.style.width = "100%";
            if (progressText) progressText.innerText = `Scan Complete! Carved ${data.artifacts.length} total artifacts.`;
            
            setTimeout(() => {
                window.location.href = `/artifacts?case_id=${caseId}`;
            }, 1000);
        } else {
            alert("Analysis failed: " + data.message);
            if (btn) btn.disabled = false;
        }
    } catch (err) {
        console.error("Scan Error:", err);
        alert("Scan execution error: " + err);
        if (btn) btn.disabled = false;
    }
}

// 2. Artifact Modal & Hex Viewer
async function openArtifactModal(artifactId) {
    const modal = document.getElementById('artifactModal');
    const modalBody = document.getElementById('artifactModalBody');
    if (!modal || !modalBody) return;

    modalBody.innerHTML = '<div style="text-align:center; padding: 30px; color: var(--text-highlight);">Loading artifact data & sector bytes...</div>';
    modal.style.display = 'flex';

    try {
        const response = await fetch(`/api/artifacts/${artifactId}`);
        const art = await response.json();

        let details = {};
        try { details = JSON.parse(art.validation_details); } catch(e){}

        let previewHtml = '';
        if (art.file_type === 'JPEG' || art.file_type === 'PNG') {
            previewHtml = `<div style="text-align:center; margin: 15px 0;"><img src="/cases/${art.case_id}/recovered/${art.filename}" style="max-width:100%; max-height: 250px; border-radius: 8px; border: 1px solid var(--border-color);"></div>`;
        } else if (art.file_type === 'TXT') {
            previewHtml = `<div style="background: var(--bg-input); padding:15px; border-radius:6px; border:1px solid var(--border-color); font-family:monospace; margin:15px 0; color: var(--accent-emerald); white-space:pre-wrap;" id="txtPreviewArea">Loading text file snippet...</div>`;
        }

        modalBody.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--border-color); padding-bottom:15px; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
                <h3 style="margin:0; color: var(--text-highlight); font-size:16px;">${art.filename} (${art.file_type})</h3>
                <span class="badge badge-${art.confidence >= 75 ? 'valid' : 'corrupt'}">${art.confidence}% CONFIDENCE</span>
            </div>

            ${previewHtml}

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; font-size:13px; margin-bottom:15px;">
                <div><strong style="color: var(--text-muted);">Case ID:</strong> ${art.case_id}</div>
                <div><strong style="color: var(--text-muted);">Sector Offset:</strong> 0x${art.offset.toString(16).toUpperCase()}</div>
                <div><strong style="color: var(--text-muted);">Size:</strong> ${art.size.toLocaleString()} Bytes</div>
                <div><strong style="color: var(--text-muted);">Validation Status:</strong> ${art.validation_status}</div>
                <div style="grid-column:span 2; word-break:break-all;"><strong style="color: var(--text-muted);">SHA-256:</strong> <code style="color: var(--text-highlight);">${art.sha256}</code></div>
            </div>

            <h4 style="color: var(--text-highlight); margin-top:15px; margin-bottom:8px; font-size:14px;">Confidence Score Breakdown:</h4>
            <ul style="font-size:12px; color: var(--text-main); margin-left:20px; margin-bottom:15px;">
                ${(details.score_breakdown || []).map(item => `<li>${item}</li>`).join('')}
            </ul>

            <h4 style="color: var(--text-highlight); margin-top:15px; margin-bottom:8px; font-size:14px;">Hex Header Inspector (First 128 Bytes):</h4>
            <div class="hex-grid" id="hexViewArea">Loading sector bytes...</div>
        `;

        // Fetch Hex preview
        const hexResp = await fetch(`/api/artifacts/${artifactId}/hex`);
        const hexData = await hexResp.json();
        const hexArea = document.getElementById('hexViewArea');
        if (hexArea) hexArea.innerText = hexData.hex_dump;

        // If text file, fetch text content for preview
        if (art.file_type === 'TXT') {
            const txtArea = document.getElementById('txtPreviewArea');
            if (txtArea) {
                const txtResp = await fetch(`/cases/${art.case_id}/recovered/${art.filename}`);
                const txtText = await txtResp.text();
                txtArea.innerText = txtText;
            }
        }

    } catch (err) {
        modalBody.innerHTML = `<div style="color: var(--accent-rose); padding:20px;">Failed to load artifact details: ${err}</div>`;
    }
}

function closeModal() {
    const modal = document.getElementById('artifactModal');
    if (modal) modal.style.display = 'none';
}

// 3. AI Assistant Query
async function submitAIQuestion(caseId) {
    const input = document.getElementById('aiInput');
    const chatContainer = document.getElementById('aiChatContainer');
    if (!input || !chatContainer || !input.value.trim()) return;

    const userQ = input.value.trim();
    input.value = '';

    // Append User Message
    chatContainer.innerHTML += `
        <div style="display:flex; justify-content:flex-end; margin-bottom:12px;">
            <div style="background: var(--bg-card-hover); color: var(--text-main); padding:10px 16px; border-radius:12px 12px 0 12px; max-width:85%; font-size:14px; border:1px solid var(--border-color);">
                ${userQ}
            </div>
        </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // Append Thinking Indicator
    const thinkId = 'think_' + Date.now();
    chatContainer.innerHTML += `
        <div id="${thinkId}" style="display:flex; margin-bottom:12px;">
            <div style="background: var(--bg-input); color: var(--text-muted); padding:10px 16px; border-radius:12px 12px 12px 0; max-width:85%; font-size:13px; border:1px solid var(--border-color);">
                Thinking...
            </div>
        </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;

    try {
        const response = await fetch('/api/ai/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ case_id: caseId, question: userQ })
        });
        const data = await response.json();

        if (document.getElementById(thinkId)) document.getElementById(thinkId).remove();

        chatContainer.innerHTML += `
            <div style="display:flex; margin-bottom:12px;">
                <div style="background: var(--bg-input); color: var(--text-highlight); padding:12px 16px; border-radius:12px 12px 12px 0; max-width:90%; font-size:14px; border:1px solid var(--accent-primary); line-height:1.5; white-space:pre-wrap;">
                    ${data.answer}
                </div>
            </div>
        `;
        chatContainer.scrollTop = chatContainer.scrollHeight;
    } catch(err) {
        if(document.getElementById(thinkId)) document.getElementById(thinkId).remove();
        chatContainer.innerHTML += `<div style="color: var(--accent-rose); font-size:12px;">AI Assistant error: ${err}</div>`;
    }
}

// 4. Safe Sanitization Simulator
function runSanitizationSim(selectId) {
    const fileSelect = document.getElementById(selectId || 'simFileSelect');
    const methodSelect = document.getElementById('simMethodSelect');
    const outputArea = document.getElementById('simOutput');
    const progressBar = document.getElementById('simProgressBar');

    if (!outputArea || !progressBar) return;

    const filename = fileSelect ? fileSelect.value : 'demo_evidence.raw';
    const method = methodSelect ? methodSelect.value : 'IEEE 2883-2022 Purge';

    outputArea.innerHTML = '[SAFE DEMO MODE] Initializing simulation pass...\n';
    progressBar.style.width = '10%';

    setTimeout(() => {
        outputArea.innerHTML += `[STEP 1] Target Selected: ${filename} (Read-Only Demo Guard active)\n`;
        outputArea.innerHTML += `[STEP 2] Algorithm Selected: ${method}\n`;
        progressBar.style.width = '40%';
    }, 600);

    setTimeout(() => {
        outputArea.innerHTML += `[STEP 3] Executing Overwrite Pass 1/3 (0x00 Pattern)...\n`;
        outputArea.innerHTML += `[STEP 4] Executing Overwrite Pass 2/3 (0xFF Pattern)...\n`;
        outputArea.innerHTML += `[STEP 5] Executing Overwrite Pass 3/3 (Pseudo-Random CSPRNG Stream)...\n`;
        progressBar.style.width = '80%';
    }, 1400);

    setTimeout(() => {
        outputArea.innerHTML += `[STEP 6] Calculating Post-Erase SHA-256 Hash Verification...\n`;
        outputArea.innerHTML += `[VERIFICATION SUCCESS] Post-Erase Sector Hash: 0000000000000000000000000000000000000000000000000000000000000000\n`;
        outputArea.innerHTML += `[AUDIT LOG] Sanitization certificate logged to audit vault.\n`;
        outputArea.innerHTML += `\n[DEMO NOTICE] Simulation complete for target '${filename}'. No physical disk hardware was altered.`;
        progressBar.style.width = '100%';
    }, 2200);
}
