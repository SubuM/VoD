import os

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Movie, PlaybackProgress
from ..schemas import ProgressIn
from ..services import streaming
from .movies import movie_out, _get_movie

router = APIRouter(tags=["player"])


@router.get("/api/movies/{movie_id}/stream")
def stream_movie(
    movie_id: int,
    range: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
):
    movie = _get_movie(db, movie_id)
    path = movie.file_path
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File no longer exists on disk")

    file_size = streaming.total_size(path)
    parsed = streaming.parse_range(range, file_size)

    if parsed is None:
        headers = {"Accept-Ranges": "bytes", "Content-Length": str(file_size)}
        return StreamingResponse(
            _file_chunks(path, 0, file_size - 1),
            media_type=streaming.video_mime_type(path),
            headers=headers,
            status_code=200,
        )

    start, end = parsed
    if start > end or start >= file_size:
        raise HTTPException(
            status_code=416,
            detail="Requested range not satisfiable",
            headers={"Content-Range": f"bytes */{file_size}"},
        )

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(end - start + 1),
    }
    return StreamingResponse(
        _file_chunks(path, start, end),
        media_type=streaming.video_mime_type(path),
        headers=headers,
        status_code=206,
    )


def _file_chunks(path: str, start: int, end: int):
    reader = streaming.RangedFileReader(path, start, end)
    try:
        yield from reader
    finally:
        reader.close()


@router.get("/api/movies/{movie_id}/progress")
def get_progress(movie_id: int, db: Session = Depends(get_db)):
    movie = _get_movie(db, movie_id)
    if movie.progress is None:
        return {"position_sec": 0.0, "duration_sec": movie.duration_sec}
    return {
        "position_sec": movie.progress.position_sec,
        "duration_sec": movie.progress.duration_sec,
    }


@router.put("/api/movies/{movie_id}/progress")
def save_progress(movie_id: int, payload: ProgressIn, db: Session = Depends(get_db)):
    movie = _get_movie(db, movie_id)
    progress = movie.progress
    if progress is None:
        progress = PlaybackProgress(movie_id=movie.id)
        db.add(progress)
    progress.position_sec = payload.position_sec
    progress.duration_sec = payload.duration_sec or movie.duration_sec
    db.commit()
    return {"saved": True}


@router.delete("/api/movies/{movie_id}/progress")
def clear_progress(movie_id: int, db: Session = Depends(get_db)):
    movie = _get_movie(db, movie_id)
    if movie.progress is not None:
        db.delete(movie.progress)
        db.commit()
    return {"deleted": True}