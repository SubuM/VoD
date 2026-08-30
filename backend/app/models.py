from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Movie(Base):
    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(index=True)
    sort_title: Mapped[str] = mapped_column(index=True)
    year: Mapped[int | None]
    file_path: Mapped[str] = mapped_column(unique=True, index=True)
    file_name: Mapped[str]
    container: Mapped[str]
    size_bytes: Mapped[int] = mapped_column(default=0)
    duration_sec: Mapped[float | None]
    width: Mapped[int | None]
    height: Mapped[int | None]
    video_codec: Mapped[str | None]
    audio_codec: Mapped[str | None]
    audio_channels: Mapped[str | None]
    poster_path: Mapped[str | None]
    backdrop_path: Mapped[str | None]
    last_modified: Mapped[float] = mapped_column(default=0)
    added_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    progress: Mapped["PlaybackProgress | None"] = relationship(
        back_populates="movie", cascade="all, delete-orphan", uselist=False
    )


class PlaybackProgress(Base):
    __tablename__ = "playback_progress"

    id: Mapped[int] = mapped_column(primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="CASCADE"), unique=True)
    position_sec: Mapped[float] = mapped_column(Float, default=0)
    duration_sec: Mapped[float | None]
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())

    movie: Mapped[Movie] = relationship(back_populates="progress")