import os
import re
from pathlib import Path

_RANGE_RE = re.compile(r"^bytes=(\d*)-(\d*)$")


def parse_range(range_header: str, file_size: int) -> tuple[int, int] | None:
    """Return (start, end) inclusive. Returns None if the header is absent or malformed."""
    if not range_header:
        return None

    m = _RANGE_RE.match(range_header.strip())
    if not m:
        return None

    start_s, end_s = m.groups()
    if not start_s:
        suffix = int(end_s) or 0
        start = max(0, file_size - suffix)
        return start, file_size - 1
    start = int(start_s)
    end = int(end_s) if end_s else file_size - 1
    end = min(end, file_size - 1)
    return start, end


class RangedFileReader:
    def __init__(self, path: str | Path, start: int, end: int, chunk_size: int = 1 << 20):
        self._file = open(path, "rb")
        self._file.seek(start)
        self._remaining = end - start + 1
        self._chunk_size = chunk_size

    def __iter__(self):
        return self

    def __next__(self):
        if self._remaining <= 0:
            raise StopIteration
        data = self._file.read(min(self._chunk_size, self._remaining))
        if not data:
            raise StopIteration
        self._remaining -= len(data)
        return data

    def close(self):
        self._file.close()


def video_mime_type(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    mapping = {
        ".mp4": "video/mp4",
        ".m4v": "video/mp4",
        ".mkv": "video/x-matroska",
        ".webm": "video/webm",
        ".avi": "video/x-msvideo",
        ".mov": "video/quicktime",
        ".wmv": "video/x-ms-wmv",
        ".ts": "video/mp2t",
        ".flv": "video/x-flv",
        ".mpg": "video/mpeg",
        ".mpeg": "video/mpeg",
    }
    return mapping.get(ext, "application/octet-stream")


def total_size(path: str | Path) -> int:
    return os.path.getsize(path)