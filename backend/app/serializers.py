from .models import Movie


def poster_url(movie: Movie) -> str:
    if movie.poster_path:
        return f"/api/movies/{movie.id}/poster"
    return None


def backdrop_url(movie: Movie) -> str:
    if movie.backdrop_path:
        return f"/api/movies/{movie.id}/backdrop"
    return None


def movie_out(movie: Movie, include_progress: bool = False) -> dict:
    data = {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "file_name": movie.file_name,
        "container": movie.container,
        "size_bytes": movie.size_bytes,
        "duration_sec": movie.duration_sec,
        "width": movie.width,
        "height": movie.height,
        "video_codec": movie.video_codec,
        "audio_codec": movie.audio_codec,
        "audio_channels": movie.audio_channels,
        "added_at": movie.added_at.isoformat(),
        "poster_url": poster_url(movie),
        "backdrop_url": backdrop_url(movie),
        "progress_sec": None,
    }
    if include_progress and movie.progress is not None:
        data["progress_sec"] = movie.progress.position_sec
        data["has_progress"] = True
    return data