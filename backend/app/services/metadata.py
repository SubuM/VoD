import json
import re
import subprocess
from pathlib import Path

_TITLE_YEAR_RE = re.compile(
    r"^(?P<title>.+?)[\._\-\s]*[\[\(]?\s*(?P<year>(?:19|20)\d{2})\s*[\]\)]?(?P<suffix>[\._\-\s]|$)",
    re.IGNORECASE,
)
_TAG_RE = re.compile(
    r"(?i)(^|[\s.\-_])(?P<tag>"
    r"(?:4k|3d|uhd|hevc|hdr(?:10)?|dolby.?vision|atmos|x264|x265|h\.?264|h\.?265|"
    r"10bit|bluray|blu-?ray|web-?dl|webrip|bdrip|brrip|dvdrip|hdtv|remux|proper|repack|"
    r"extended|directors?.?cut|imax|aac|ac3|dts|dd5\.1|uncut)"
    r")([\s.\-_]|$)",
    re.IGNORECASE,
)
_MULTI_SPACE_RE = re.compile(r"\s+")

KNOWN_TAGS = {
    "aac", "ac3", "atmos", "bdrip", "blu-ray", "bluray", "brrip", "dolby vision",
    "directors cut", "dts", "dvdrip", "extended", "h264", "h265", "hdr", "hdr10",
    "hdtv", "hevc", "imax", "proper", "remux", "repack", "uhd", "uncut", "web-dl",
    "webrip", "x264", "x265", "10bit", "3d", "4k",
}


def parse_filename(file_name: str) -> tuple[str, int | None]:
    stem = Path(file_name).stem
    year: int | None = None

    m = _TITLE_YEAR_RE.match(stem)
    if m:
        title_part = m.group("title")
        year = int(m.group("year"))
    else:
        title_part = stem

    title = _TAG_RE.sub(" ", title_part)
    title = title.replace("_", " ").replace(".", " ").replace("-", " ")
    title = _MULTI_SPACE_RE.sub(" ", title).strip()
    title = title.strip(" ._-[]()")

    if not title:
        title = stem
    if year is None:
        year_match = re.search(r"(?<![0-9])((?:19|20)\d{2})(?![0-9])", stem)
        if year_match:
            year = int(year_match.group(1))

    return title, year


def sort_key_for(title: str) -> str:
    title = title.lower()
    articles = ("the ", "a ", "an ")
    for article in articles:
        if title.startswith(article) and len(title) > len(article):
            title = title[len(article):]
            break
    return re.sub(r"[^a-z0-9]+", "", title) or title


def probe_video(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams",
        path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)

    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})

    duration = None
    if fmt.get("duration"):
        duration = float(fmt["duration"])
    elif video and video.get("duration"):
        duration = float(video["duration"])

    return {
        "duration_sec": duration,
        "width": int(video["width"]) if video and video.get("width") else None,
        "height": int(video["height"]) if video and video.get("height") else None,
        "video_codec": video.get("codec_name") if video else None,
        "audio_codec": audio.get("codec_name") if audio else None,
        "audio_channels": audio.get("channel_layout") if audio else None,
        "size_bytes": int(fmt.get("size") or 0),
    }


def extract_poster(video_path: str, target_path: Path, width: int = 400, at_frac: float = 0.08) -> bool:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _seek_before_black(
        video_path, at_frac, int(_probe_duration(video_path))
    )
    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-ss", f"{timestamp:.1f}",
        "-i", video_path,
        "-frames:v", "1",
        "-vf", f"scale={width}:-2",
        str(target_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and target_path.exists() and target_path.stat().st_size > 0
    except Exception:
        return False


def extract_backdrop(video_path: str, target_path: Path, width: int = 1280, at_frac: float = 0.2) -> bool:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _seek_before_black(
        video_path, at_frac, int(_probe_duration(video_path))
    )
    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-ss", f"{timestamp:.1f}",
        "-i", video_path,
        "-frames:v", "1",
        "-vf", f"scale={width}:-2",
        str(target_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0 and target_path.exists() and target_path.stat().st_size > 0
    except Exception:
        return False


def _probe_duration(video_path: str) -> float:
    try:
        info = probe_video(video_path)
        return float(info.get("duration_sec") or 0)
    except Exception:
        return 0


def _seek_before_black(video_path: str, frac: float, duration: int) -> float:
    """Avoid grabbing a pure-black frame (opening credits) by nudging slightly in."""
    target = max(1.0, duration * frac)
    cmd = [
        "ffmpeg", "-v", "error",
        "-ss", f"{target:.1f}",
        "-i", video_path,
        "-frames:v", "1",
        "-vf", "scale=16:16,format=gray,blackframe=0",
        "-f", "null", "-",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        for line in result.stderr.splitlines():
            if "blackframe" in line:
                m = re.search(r"pts:(\d+)", line)
                if m:
                    return max(0.0, target - 1.0)
    except Exception:
        pass
    return target