import hashlib

def calculate_sha256(file_path, chunk_size=65536):
    """
    Computes streaming SHA-256 hash of a target disk image file.
    Reads in 64KB chunks to ensure safe memory consumption.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()

def calculate_bytes_sha256(data_bytes):
    """
    Computes SHA-256 hash of byte array artifact.
    """
    return hashlib.sha256(data_bytes).hexdigest()
