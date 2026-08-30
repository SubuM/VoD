from datetime import datetime
from typing import Annotated

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field


class MovieOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    year: int | None
    file_name: str
    container: str
    size_bytes: int
    duration_sec: float | None
    width: int | None
    height: int | None
    video_codec: str | None
    audio_codec: str | None
    audio_channels: str | None
    added_at: datetime
    poster_url: str | None = None
    backdrop_url: str | None = None
    progress_sec: float | None = Field(default=None, exclude=True)


class MovieListItem(MovieOut):
    progress_sec: float | None = None


class MovieDetail(MovieOut):
    progress_sec: float | None = None
    has_progress: bool = False


class ProgressIn(BaseModel):
    position_sec: float = Field(ge=0)
    duration_sec: float | None = Field(default=None, ge=0)


class LibraryStatus(BaseModel):
    movie_count: int
    total_size_bytes: int
    media_dirs: list[str]
    scan_running: bool


class PagedMovies(BaseModel):
    items: list[MovieOut]
    total: int
    page: int
    page_size: int


SortOrder = Annotated[str, Query(pattern="^(added|title|year|random)$")]
YearFilter = Annotated[int | None, Query(ge=1800, le=2100)]
Page = Annotated[int, Query(ge=1)]
PageSize = Annotated[int, Query(ge=1, le=100)]