# File Signatures Database for Signature-Based Carving

FILE_SIGNATURES = {
    'JPEG': {
        'extension': '.jpg',
        'mime': 'image/jpeg',
        'header': b'\xFF\xD8\xFF',
        'footer': b'\xFF\xD9',
        'max_search_size': 10 * 1024 * 1024, # Max 10MB
        'default_size': 500 * 1024
    },
    'PNG': {
        'extension': '.png',
        'mime': 'image/png',
        'header': b'\x89PNG\r\n\x1a\n',
        'footer': b'IEND\xaeB\x60\x82',
        'max_search_size': 15 * 1024 * 1024,
        'default_size': 500 * 1024
    },
    'PDF': {
        'extension': '.pdf',
        'mime': 'application/pdf',
        'header': b'%PDF-',
        'footer': b'%%EOF',
        'max_search_size': 25 * 1024 * 1024,
        'default_size': 1 * 1024 * 1024
    },
    'ZIP': {
        'extension': '.zip',
        'mime': 'application/zip',
        'header': b'PK\x03\x04',
        'footer': b'PK\x05\x06',
        'max_search_size': 30 * 1024 * 1024,
        'default_size': 2 * 1024 * 1024
    },
    'TXT': {
        'extension': '.txt',
        'mime': 'text/plain',
        'header': b'--- FORENSIC TEXT DOCUMENT ---',
        'footer': b'--- END FORENSIC TEXT ---',
        'max_search_size': 1 * 1024 * 1024,
        'default_size': 50 * 1024
    }
}
