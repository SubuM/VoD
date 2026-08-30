import os

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..models import Movie, PlaybackProgress
from ..schemas import MovieDetail, MovieListItem, PagedMovies, Page, PageSize, SortOrder, YearFilter
from ..serializers import movie_out
from ..services import search as search_service

router = APIRouter(prefix="/api/movies", tags=["movies"])


def _get_movie(db: Session, movie_id: int) -> Movie:
    movie = db.scalar(
        select(Movie).options(joinedload(Movie.progress)).where(Movie.id == movie_id)
    )
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("", response_model=PagedMovies)
def list_movies(
    db: Session = Depends(get_db),
    sort: SortOrder = "added",
    year: YearFilter = None,
    search: str | None = None,
    page: Page = 1,
    page_size: PageSize = 40,
):
    base = select(Movie).options(joinedload(Movie.progress))
    filters = []
    if year:
        filters.append(Movie.year == year)
    if search:
        base = base.where(Movie.id.in_(
            [m.id for m in search_service.search_movies(db, search, year=year, limit=1000)]
        ))
        filters = []
    for f in filters:
        base = base.where(f)

    if sort == "title":
        base = base.order_by(Movie.sort_title.asc(), Movie.year.asc())
    elif sort == "year":
        base = base.order_by(Movie.year.desc().nulls_last(), Movie.sort_title.asc())
    elif sort == "random":
        base = base.order_by(func.random())
    else:
        base = base.order_by(Movie.added_at.desc())

    total = len(db.scalars(base).all())
    items = db.scalars(base.offset((page - 1) * page_size).limit(page_size)).unique().all()
    return PagedMovies(
        items=[MovieListItem(**movie_out(m, include_progress=True)) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/continue-watching", response_model=list[MovieListItem])
def continue_watching(db: Session = Depends(get_db)):
    movies = db.scalars(
        select(Movie)
        .join(PlaybackProgress, PlaybackProgress.movie_id == Movie.id)
        .order_by(PlaybackProgress.updated_at.desc())
        .limit(20)
    ).unique().all()
    return [MovieListItem(**movie_out(m, include_progress=True)) for m in movies]


@router.get("/{movie_id}", response_model=MovieDetail)
def movie_detail(movie_id: int, db: Session = Depends(get_db)):
    return MovieDetail(**movie_out(_get_movie(db, movie_id), include_progress=True))


@router.get("/{movie_id}/poster")
def movie_poster(movie_id: int, db: Session = Depends(get_db)):
    return _serve_art(_get_movie(db, movie_id), "poster_path", "poster")


@router.get("/{movie_id}/backdrop")
def movie_backdrop(movie_id: int, db: Session = Depends(get_db)):
    return _serve_art(_get_movie(db, movie_id), "backdrop_path", "backdrop")


def _serve_art(movie: Movie, attr: str, kind: str):
    from fastapi.responses import FileResponse

    path = getattr(movie, attr)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"{kind} not available")
    return FileResponse(path, media_type="image/jpeg", filename=f"{kind}-{movie.id}.jpg")