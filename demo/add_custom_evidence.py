import sys
import os
import random

DEMO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
DEMO_IMAGE_PATH = os.path.join(DEMO_DIR, 'demo_evidence.raw')

def embed_custom_file(file_name, text_content="--- FORENSIC TEXT DOCUMENT ---\nJUDGES DEMO FILE: Live Recovery Test\nCONFIDENTIAL EVIDENCE FOR HACKATHON EVALUATION\n--- END FORENSIC TEXT ---"):
    """
    Appends a custom file payload into the synthetic disk image `demo_evidence.raw`.
    This allows live embedding of custom judge test files during presentation.
    """
    os.makedirs(DEMO_DIR, exist_ok=True)

    if not os.path.exists(DEMO_IMAGE_PATH):
        from demo.generate_demo_evidence import generate_demo_disk_image
        generate_demo_disk_image()

    with open(DEMO_IMAGE_PATH, 'rb') as f:
        disk_data = bytearray(f.read())

    # Format content bytes
    if isinstance(text_content, str):
        if not text_content.startswith("--- FORENSIC TEXT DOCUMENT ---"):
            text_content = f"--- FORENSIC TEXT DOCUMENT ---\nFILENAME: {file_name}\n{text_content}\n--- END FORENSIC TEXT ---"
        file_bytes = text_content.encode('utf-8')
    else:
        file_bytes = text_content

    # Add random cluster slack space
    slack_size = random.randint(1024, 2048)
    disk_data.extend(b'\x00' * slack_size)

    start_offset = len(disk_data)
    disk_data.extend(file_bytes)
    disk_data.extend(b'\x00' * 4096)

    with open(DEMO_IMAGE_PATH, 'wb') as f:
        f.write(disk_data)

    print(f"[OK] Custom file '{file_name}' embedded into disk image!")
    print(f"     Offset: 0x{start_offset:X} | Size: {len(file_bytes)} bytes")
    print(f"     Updated Disk Image Path: {DEMO_IMAGE_PATH}")

if __name__ == '__main__':
    name = sys.argv[1] if len(sys.argv) > 1 else "Judges_Live_Evidence.txt"
    content = sys.argv[2] if len(sys.argv) > 2 else "Judges Secret Verification Code: #SIH2026-WINNER-99"
    embed_custom_file(name, content)
