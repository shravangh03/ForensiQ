import os
from .signatures import FILE_SIGNATURES

class FileCarver:
    def __init__(self, image_path):
        self.image_path = image_path
        self.file_size = os.path.getsize(image_path)

    def scan_and_extract(self, progress_callback=None):
        """
        Reads the disk image file in READ-ONLY mode and extracts carved file candidates.
        """
        candidates = []
        
        with open(self.image_path, 'rb') as f:
            data = f.read()

        total_bytes = len(data)
        scanned_offsets = set()

        for file_type, sig in FILE_SIGNATURES.items():
            header = sig['header']
            footer = sig['footer']
            max_size = sig['max_search_size']

            start_pos = 0
            while start_pos < total_bytes:
                header_pos = data.find(header, start_pos)
                if header_pos == -1:
                    break

                # Advance start_pos past current header to prevent infinite loops
                start_pos = header_pos + len(header)

                if header_pos in scanned_offsets:
                    continue

                end_pos = -1
                if footer:
                    # Require minimum payload size before footer search (e.g. 50 bytes)
                    footer_search_start = header_pos + min(len(header) + 20, total_bytes - header_pos)
                    search_limit = min(total_bytes, header_pos + max_size)
                    
                    # For JPEG / PDF, search for the last footer within search_limit or first valid footer
                    if file_type == 'JPEG':
                        # Find end marker \xFF\xD9
                        f_pos = data.find(footer, footer_search_start, search_limit)
                        if f_pos != -1:
                            end_pos = f_pos + len(footer)
                    elif file_type == 'PNG':
                        f_pos = data.find(footer, footer_search_start, search_limit)
                        if f_pos != -1:
                            end_pos = f_pos + len(footer)
                    elif file_type == 'PDF':
                        f_pos = data.find(footer, footer_search_start, search_limit)
                        if f_pos != -1:
                            end_pos = f_pos + len(footer)
                    elif file_type == 'TXT':
                        f_pos = data.find(footer, footer_search_start, search_limit)
                        if f_pos != -1:
                            end_pos = f_pos + len(footer)

                if end_pos != -1 and end_pos > header_pos:
                    carved_size = end_pos - header_pos
                    extracted_bytes = data[header_pos:end_pos]
                    start_pos = max(start_pos, end_pos) # Jump start_pos past extracted candidate
                else:
                    carved_size = min(sig['default_size'], total_bytes - header_pos)
                    extracted_bytes = data[header_pos:header_pos + carved_size]

                scanned_offsets.add(header_pos)

                candidates.append({
                    'file_type': file_type,
                    'offset': header_pos,
                    'size': carved_size,
                    'raw_bytes': extracted_bytes,
                    'extension': sig['extension'],
                    'mime': sig['mime']
                })

                if progress_callback:
                    progress = int((header_pos / total_bytes) * 100)
                    progress_callback(progress)

        # Sort candidates by offset
        candidates.sort(key=lambda x: x['offset'])
        return candidates
