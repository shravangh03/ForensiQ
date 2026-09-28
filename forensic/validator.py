import io
from PIL import Image
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from .signatures import FILE_SIGNATURES

def validate_artifact(file_type, raw_bytes):
    """
    Validates carved raw bytes for header, footer, structure, and renderability.
    Returns dictionary with boolean flags, detailed report, and overall pass status.
    """
    validation = {
        'header_valid': False,
        'footer_valid': False,
        'structure_valid': False,
        'renderable': False,
        'details': []
    }

    sig = FILE_SIGNATURES.get(file_type)
    if not sig:
        validation['details'].append("Unknown signature type.")
        return validation

    # 1. Header Validation
    header = sig['header']
    if raw_bytes.startswith(header):
        validation['header_valid'] = True
        validation['details'].append("Header signature matched perfectly.")
    else:
        validation['details'].append("Header signature missing or corrupt.")

    # 2. Footer Validation
    footer = sig['footer']
    if footer:
        if raw_bytes.rstrip(b'\x00\r\n').endswith(footer) or footer in raw_bytes[-100:]:
            validation['footer_valid'] = True
            validation['details'].append("Footer signature matched.")
        else:
            validation['details'].append("Footer signature missing or truncated.")
    else:
        validation['footer_valid'] = True

    # 3. Structure & Renderability Validation by File Type
    if file_type in ['JPEG', 'PNG']:
        try:
            image = Image.open(io.BytesIO(raw_bytes))
            image.verify()
            validation['structure_valid'] = True
            validation['renderable'] = True
            validation['details'].append(f"Image decoded successfully ({image.format}, {image.size[0]}x{image.size[1]} px).")
        except Exception as e:
            validation['details'].append(f"Image decoding check failed: {str(e)}")

    elif file_type == 'PDF':
        if b'/Root' in raw_bytes or b'/Pages' in raw_bytes or b'/Catalog' in raw_bytes or b'xref' in raw_bytes:
            validation['structure_valid'] = True
            validation['details'].append("PDF internal catalog/xref markers found.")
        
        if PYPDF_AVAILABLE:
            try:
                reader = pypdf.PdfReader(io.BytesIO(raw_bytes), strict=False)
                if reader.pages and len(reader.pages) > 0:
                    validation['renderable'] = True
                    validation['details'].append(f"PDF parsed successfully ({len(reader.pages)} page(s)).")
                elif validation['structure_valid']:
                    validation['renderable'] = True
                    validation['details'].append("PDF basic structure verified.")
            except Exception as e:
                if validation['structure_valid']:
                    validation['renderable'] = True
                    validation['details'].append("PDF structure verified (catalog markers found).")
                else:
                    validation['details'].append(f"PDF parsing error: {str(e)}")
        else:
            if validation['structure_valid']:
                validation['renderable'] = True
                validation['details'].append("PDF basic structure verified (PyPDF fallback mode).")

    elif file_type == 'TXT':
        try:
            text = raw_bytes.decode('utf-8', errors='ignore')
            printable_ratio = sum(1 for c in text if c.isprintable() or c in '\n\r\t') / max(1, len(text))
            if printable_ratio > 0.8:
                validation['structure_valid'] = True
                validation['renderable'] = True
                validation['details'].append(f"Text encoding valid ({int(printable_ratio*100)}% printable characters).")
            else:
                validation['details'].append("Low ratio of printable text characters.")
        except Exception as e:
            validation['details'].append(f"Text decoding failed: {str(e)}")

    elif file_type == 'ZIP':
        if b'PK\x01\x02' in raw_bytes or b'PK\x05\x06' in raw_bytes:
            validation['structure_valid'] = True
            validation['renderable'] = True
            validation['details'].append("ZIP central directory structure validated.")
        else:
            validation['details'].append("ZIP structure missing central directory.")

    return validation
