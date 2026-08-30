import binascii
import logging
import os
import threading
from pathlib import Path

from sqlalchemy import select

from ..config import VIDEO_EXTENSIONS, get_settings
from ..database import SessionLocal
from ..models import Movie
from . import metadata

logger = logging.getLogger(__name__)

_scan_lock = threading.Lock()
_scan_running = False


def scan_running() -> bool:
    return _scan_running


def _iter_movie_files():
    seen = set()
    for media_dir in get_settings().media_dirs:
        root = Path(media_dir)
        if not root.exists():
            logger.warning("Media directory does not exist: %s", root)
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for name in filenames:
                path = Path(dirpath) / name
                ext = path.suffix.lower()
                if ext in VIDEO_EXTENSIONS and not name.startswith("."):
                    if path.resolve() not in seen:
                        seen.add(path.resolve())
                        yield path


def scan_library(force: bool = False) -> dict:
    global _scan_running
    if not _scan_lock.acquire(blocking=False):
        return {"started": False, "reason": "scan_already_running"}

    _scan_running = True
    added, updated, removed = 0, 0, 0
    try:
        scanned_paths = set()
        with SessionLocal() as db:
            for file_path in _iter_movie_files():
                scanned_paths.add(file_path)
                result = _index_file(db, file_path, force)
                if result == "added":
                    added += 1
                elif result == "updated":
                    updated += 1

            for movie in db.scalars(select(Movie)).all():
                if Path(movie.file_path) not in scanned_paths:
                    db.delete(movie)
                    removed += 1
            db.commit()
    except Exception:
        logger.exception("Library scan failed")
    finally:
        _scan_running = False
        _scan_lock.release()

    return {"started": True, "added": added, "updated": updated, "removed": removed}


def _index_file(db, file_path: Path, force: bool) -> str | None:
    stat = file_path.stat()
    mtime = stat.st_mtime
    existing = db.scalar(select(Movie).where(Movie.file_path == str(file_path)))

    if existing is not None and not force and abs(existing.last_modified - mtime) < 1 and existing.size_bytes == stat.st_size:
        return

    try:
        info = metadata.probe_video(str(file_path))
    except Exception:
        logger.warning("Could not probe %s, skipping", file_path)
        return

    title, year = metadata.parse_filename(file_path.name)
    settings = get_settings()
    art_key = _art_key(file_path)

    poster = _generate_art(
        file_path, art_key, "poster", settings.thumbs_width, 0.08
    )
    backdrop = _generate_art(
        file_path, art_key, "backdrop", settings.backdrops_width, 0.2
    )

    if existing is None:
        db.add(
            Movie(
                title=title,
                sort_title=metadata.sort_key_for(title),
                year=year,
                file_path=str(file_path),
                file_name=file_path.name,
                container=file_path.suffix.lstrip(".").lower(),
                size_bytes=info["size_bytes"],
                duration_sec=info["duration_sec"],
                width=info["width"],
                height=info["height"],
                video_codec=info["video_codec"],
                audio_codec=info["audio_codec"],
                audio_channels=info["audio_channels"],
                poster_path=poster,
                backdrop_path=backdrop,
                last_modified=mtime,
            )
        )
        db.flush()
        return "added"
    else:
        existing.title = title
        existing.sort_title = metadata.sort_key_for(title)
        existing.year = year
        existing.file_name = file_path.name
        existing.size_bytes = info["size_bytes"]
        existing.duration_sec = info["duration_sec"]
        existing.width = info["width"]
        existing.height = info["height"]
        existing.video_codec = info["video_codec"]
        existing.audio_codec = info["audio_codec"]
        existing.audio_channels = info["audio_channels"]
        existing.poster_path = poster or existing.poster_path
        existing.backdrop_path = backdrop or existing.backdrop_path
        existing.last_modified = mtime
        return "updated"

    return None


def _art_key(video_path: Path) -> str:
    return f"m{binascii.crc32(str(video_path).encode()) & 0xFFFFFFFF}"


def _generate_art(video_path: Path, key: str, kind: str, width: int, frac: float) -> str | None:
    settings = get_settings()
    cache_dir = Path(settings.data_dir) / (kind + "s")
    target = cache_dir / f"{key}.jpg"

    if target.exists():
        return str(target)

    extractor = metadata.extract_backdrop if kind == "backdrop" else metadata.extract_poster
    if extractor(str(video_path), target, width=width, at_frac=frac):
        return str(target)
    return None