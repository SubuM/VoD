import os
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import Movie
from ..schemas import LibraryStatus
from ..services import scanner

router = APIRouter(prefix="/api/library", tags=["library"])


@router.get("/status", response_model=LibraryStatus)
def library_status(db: Session = Depends(get_db)):
    row = db.execute(
        select(func.count(Movie.id), func.coalesce(func.sum(Movie.size_bytes), 0))
    ).one()
    return LibraryStatus(
        movie_count=row[0],
        total_size_bytes=row[1],
        media_dirs=[d for d in get_settings().media_dirs if Path(d).exists()],
        scan_running=scanner.scan_running(),
    )


@router.post("/rescan")
def trigger_rescan(force: bool = False):
    result = scanner.scan_library(force=force)
    return result