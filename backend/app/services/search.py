import re

from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from ..models import Movie

FTS_SPECIAL = re.compile(r'["*^(){}:&|]+')


def search_movies(db: Session, query: str, year: int | None = None, limit: int = 50) -> list[Movie]:
    query = query.strip()
    if not query:
        return []

    fts_query = _build_fts_query(query, year)
    if fts_query:
        try:
            return _run_fts(db, fts_query, year, limit)
        except Exception:
            pass
    return _like_lookup(db, query, year, limit)


def _build_fts_query(query: str, year: int | None) -> str | None:
    tokens = [FTS_SPECIAL.sub("", t) for t in query.split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return None

    parts = []
    for token in tokens:
        if token.isdigit() and len(token) == 4:
            parts.append(f"year:{token}*")
        else:
            parts.append(f'"{token}"*')
    if year:
        parts.append(f"year:{year}")
    return " AND ".join(parts)


def _run_fts(db: Session, fts_query: str, year: int | None, limit: int) -> list[Movie]:
    ids_sql = (
        f"SELECT rowid FROM movies_fts WHERE movies_fts MATCH :q"
        f" ORDER BY bm25(movies_fts, 1.0, 1.0, 8.0) LIMIT :lim"
    )
    ids = list(db.execute(text(ids_sql), {"q": fts_query, "lim": limit}).scalars())

    if not ids:
        return []

    stmt = (
        select(Movie)
        .options(joinedload(Movie.progress))
        .where(Movie.id.in_(ids))
    )
    movies = list(db.scalars(stmt).unique().all())
    order = {movie_id: index for index, movie_id in enumerate(ids)}
    movies.sort(key=lambda m: order.get(m.id, len(ids)))
    return movies


def _like_lookup(db: Session, query: str, year: int | None, limit: int) -> list[Movie]:
    like = f"%{query.lower()}%"
    stmt = select(Movie).where(Movie.title.ilike(like)).limit(limit)
    if year:
        stmt = stmt.where(Movie.year == year)
    return list(db.scalars(stmt))