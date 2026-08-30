from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v", ".wmv", ".ts", ".flv", ".mpg", ".mpeg"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FlashView"
    media_dir: str = "movies"
    extra_media_dirs: str = ""
    data_dir: str = "./data"
    port: int = 8000
    auto_rescan: bool = True
    rescan_interval_sec: int = 30
    thumbs_width: int = 400
    backdrops_width: int = 1280

    @property
    def db_path(self) -> str:
        return f"{self.data_dir}/library.db"

    @property
    def posters_dir(self) -> str:
        return f"{self.data_dir}/posters"

    @property
    def backdrops_dir(self) -> str:
        return f"{self.data_dir}/backdrops"

    @property
    def media_dirs(self) -> list[str]:
        dirs = [self.media_dir]
        dirs += [d.strip() for d in self.extra_media_dirs.split(",") if d.strip()]
        return [d for d in dirs if d]


@lru_cache
def get_settings() -> Settings:
    return Settings()