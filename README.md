# FlashView

A small, self-hosted, **completely free** media server that mimics the core Plex experience for a movie library. Built for a Raspberry Pi 4 and powered by tools that cost nothing and track nobody.

- **Backend** — FastAPI (Python), direct-play streaming with HTTP `Range` support (no transcoding needed, perfect for a Pi)
- **Frontend** — Vite + React with a hand-rolled, Plex-like dark UI that is easy to restyle
- **Database** — SQLite with **FTS5 full-text search**, WAL mode, resume/progress tracking, "continue watching"
- **Metadata** — 100% free and local: smart filename parsing plus real poster/backdrop frames extracted from the video itself with `ffmpeg` (no API keys, no internet)

## Feature summary

| Feature | How it works |
| --- | --- |
| Library scanning | Auto-scans your USB movie folders on boot, then every 30 s; manual rescan via UI/API |
| Movie metadata | Filename → title + year (`Dune - Part Two.2024.mp4` → "Dune Part Two", 2024) |
| Posters & backdrops | Extracted frames from each video and cached (no TMDB account, no key) |
| Streaming | Direct play with byte-range requests → instant seek, any device/browser |
| Search | SQLite FTS5 (fast prefix + year queries), auto-fallback to `LIKE` |
| Continue watching | Per-user progress saved every 5 s during playback, resume from detail page |
| Advanced sort/filter | Recently added, title, year, random; year filter |

## Requirements

- Python 3.11+
- Node 18+ (only to build the frontend)
- `ffmpeg` + `ffprobe` (framegrabs + duration/codec probing)
- A folder of movie files (e.g. a mounted USB drive)

## Run on the Pi (recommended)

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg python3-venv git
git clone <your-repo-url> flashview
cd flashview
bash deploy/setup_pi.sh
```

The script installs dependencies, builds the frontend, writes `backend/.env`
(points `MEDIA_DIR` at `/media/usb/movies`), and registers a `flashview`
systemd service. Then mount your USB drive onto `$MEDIA_DIR`, add movie files,
and open `http://<raspberry-pi-ip>:8000`.

Useful commands:

```bash
systemctl status flashview        # service status
journalctl -u flashview -f        # live logs
curl -X POST http://<pi-ip>:8000/api/library/rescan?force=true   # rescan now
```

## Run with Docker (optional)

```bash
docker compose up -d --build
# frontend on http://<host>:8080 , API on :8000
```

Edit the media volume mount in `docker-compose.yml` to match your USB drive.

## Run locally (development)

```bash
# 1. Backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp backend/.env.example backend/.env        # set MEDIA_DIR to a folder of movies
bash backend/run.sh                          # http://127.0.0.1:8000

# 2. Frontend (another terminal)
cd frontend
npm install
npm run dev                                  # http://127.0.0.1:5173 (proxies /api)
```

For production without Docker, build the frontend once and the backend serves it all
on a single port:

```bash
cd frontend && npm ci && npm run build
cd ../backend && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration (`backend/.env`)

| Variable | Default | Description |
| --- | --- | --- |
| `MEDIA_DIR` | `movies` | Folder(s) holding your movies; can be a USB mount path |
| `EXTRA_MEDIA_DIRS` | *(empty)* | Comma-separated extra folders to scan |
| `DATA_DIR` | `./data` | Where the SQLite DB and generated art are cached |
| `PORT` | `8000` | Server port |
| `AUTO_RESCAN` | `true` | Background re-scan every 30 s |

## API overview

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Liveness |
| `GET` | `/api/library/status` | Movie count, size, configured dirs |
| `POST` | `/api/library/rescan?force=` | Trigger a scan |
| `GET` | `/api/movies` | List / search / sort / filter, paginated |
| `GET` | `/api/movies/continue-watching` | Resumable items, newest first |
| `GET` | `/api/movies/{id}` | Detail |
| `GET` | `/api/movies/{id}/stream` | Video stream with `Range` support |
| `GET` | `/api/movies/{id}/poster` `/backdrop` | Cached framegrab art |
| `PUT/DELETE` | `/api/movies/{id}/progress` | Save / clear playback position |

Interactive API docs at `/docs`.

## Customizing the look

All colors, spacing, and fonts live in `frontend/src/styles.css` as CSS custom
properties (`--bg`, `--accent`, `--radius`, …). Change the theme in one place,
or replace the handcrafted components inside `frontend/src/` — every screen is
plain React, no UI framework to fight.

## Roadmap ideas

- TV shows (per-season folder layout, episode scraping)
- Multiple libraries / users
- Transcoding for weak clients (ffmpeg HLS on demand)
- Trakt/TMDB metadata fetching (optional, still free)
- Mobile-friendly cast UI