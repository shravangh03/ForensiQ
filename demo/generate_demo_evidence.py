import os
import io
import random
from PIL import Image, ImageDraw, ImageFont

# Path to output synthetic disk image
DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DEMO_IMAGE_PATH = os.path.join(DEMO_DIR, 'demo_evidence.raw')

def create_sample_jpeg(filename_label, width=200, height=150, color=(0, 242, 254)):
    """Generates a valid JPEG image binary."""
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([10, 10, width-10, height-10], outline=(255, 255, 255), width=3)
    draw.text((20, height//2 - 10), filename_label, fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

def create_sample_png(filename_label, width=200, height=150, color=(16, 185, 129)):
    """Generates a valid PNG image binary."""
    img = Image.new('RGBA', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    draw.ellipse([20, 20, width-20, height-20], fill=(255, 255, 255, 100), outline=(255, 255, 255))
    draw.text((30, height//2 - 10), filename_label, fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()

def create_sample_pdf(title, body_text):
    """Generates a minimal valid PDF binary."""
    pdf_content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kinds [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length 120 >>
stream
BT
/F1 18 Tf
50 700 Td
({title}) Tj
/F1 12 Tf
0 -30 Td
({body_text}) Tj
ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000260 00000 n 
0000000430 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
510
%%EOF"""
    return pdf_content.encode('utf-8')

def create_sample_txt(header_label, body_lines):
    """Generates a valid forensic text file binary."""
    content = f"--- FORENSIC TEXT DOCUMENT ---\n"
    content += f"LABEL: {header_label}\n"
    content += "-------------------------------\n"
    for line in body_lines:
        content += f"{line}\n"
    content += "--- END FORENSIC TEXT ---\n"
    return content.encode('utf-8')

def generate_demo_disk_image():
    """
    Stitches multiple valid file binaries separated by zero-padding and noise sectors
    into a raw unformatted disk image file (`demo_evidence.raw`).
    """
    os.makedirs(DEMO_DIR, exist_ok=True)
    
    print("[+] Generating synthetic files for disk image...")
    artifacts = [
        ("Evidence_Photo_01.jpg", create_sample_jpeg("CONFIDENTIAL EVID-1", color=(239, 68, 68))),
        ("Suspect_Identity.png", create_sample_png("SUSPECT_PASSPORT", color=(59, 130, 246))),
        ("Warrant_Details.pdf", create_sample_pdf("SEARCH WARRANT #9921", "Court Order for Digital Evidence Extraction")),
        ("Forensic_Notes.txt", create_sample_txt("CASE NOTES", ["Suspect attempted file deletion at 14:22.", "Recovered artifacts include images and PDFs."])),
        ("Evidence_Photo_02.jpg", create_sample_jpeg("CRIME SCENE #2", color=(168, 85, 247))),
        ("Financial_Ledger.pdf", create_sample_pdf("FINANCIAL AUDIT 2026", "Transaction log of unauthorized access")),
        ("Network_Logs.txt", create_sample_txt("IP LOGS", ["192.168.1.105 - AUTH SUCCESS", "10.0.0.42 - FILE ACCESSED"])),
        ("Backup_Chart.png", create_sample_png("NETWORK DIAGRAM", color=(16, 185, 129))),
    ]

    print("[+] Creating raw disk image (demo_evidence.raw)...")
    disk_buffer = bytearray()

    # Initial boot sector / partition table noise block (4KB)
    disk_buffer.extend(os.urandom(4096))

    for name, data_bytes in artifacts:
        # Add cluster alignment zero slack (512 to 2048 bytes of noise/zeros)
        slack_size = random.randint(1024, 4096)
        disk_buffer.extend(b'\x00' * slack_size)
        
        # Write actual file payload
        print(f"    -> Embedding {name} ({len(data_bytes):,} bytes) at offset 0x{len(disk_buffer):X}")
        disk_buffer.extend(data_bytes)

    # Trailing raw disk sector noise (8KB)
    disk_buffer.extend(b'\x00' * 8192)

    with open(DEMO_IMAGE_PATH, 'wb') as f:
        f.write(disk_buffer)

    total_size = len(disk_buffer)
    print(f"[OK] Demo evidence disk image created successfully!")
    print(f"    Path: {DEMO_IMAGE_PATH}")
    print(f"    Total Disk Image Size: {total_size:,} bytes ({total_size / 1024:.2f} KB)")
    return DEMO_IMAGE_PATH

if __name__ == '__main__':
    generate_demo_disk_image()
