import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from .config import get_settings
from .database import init_db
from .routes import library, movies, player
from .services import scanner
from .services.watcher import LibraryWatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()
watcher = LibraryWatcher(settings.rescan_interval_sec)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if settings.auto_rescan:
        threading.Thread(target=scanner.scan_library, name="initial-scan", daemon=True).start()
    watcher.start()
    yield
    watcher.stop()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(player.router)
app.include_router(library.router)


@app.get("/api/health")
def health():
    from .services.scanner import scan_running

    return {"status": "ok", "app": settings.app_name, "scan_running": scan_running()}


dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if dist.exists():

    class SPAStaticFiles(StaticFiles):
        async def get_response(self, path: str, scope):
            try:
                return await super().get_response(path, scope)
            except HTTPException as exc:
                if exc.status_code == 404:
                    return await super().get_response("index.html", scope)
                raise

    app.mount("/", SPAStaticFiles(directory=dist, html=True), name="frontend")