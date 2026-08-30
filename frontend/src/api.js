async function json(res) {
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`${res.status} ${res.statusText} ${body}`.trim());
  }
  return res.json();
}

export async function getMovies(params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') qs.set(k, v);
  });
  const res = await fetch(`/api/movies?${qs}`);
  return json(res);
}

export async function getMovie(id) {
  return json(await fetch(`/api/movies/${id}`));
}

export async function getContinueWatching() {
  return json(await fetch('/api/movies/continue-watching'));
}

export async function getLibraryStatus() {
  return json(await fetch('/api/library/status'));
}

export async function rescan(force = false) {
  return json(await fetch(`/api/library/rescan?force=${force}`, { method: 'POST' }));
}

export async function getProgress(id) {
  return json(await fetch(`/api/movies/${id}/progress`));
}

export async function saveProgress(id, positionSec, durationSec) {
  return json(
    await fetch(`/api/movies/${id}/progress`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ position_sec: positionSec, duration_sec: durationSec }),
    }),
  );
}

export async function clearProgress(id) {
  return json(await fetch(`/api/movies/${id}/progress`, { method: 'DELETE' }));
}

export function streamUrl(id) {
  return `/api/movies/${id}/stream`;
}

export function formatDuration(sec) {
  if (!sec && sec !== 0) return '—';
  const s = Math.round(sec);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const r = Math.floor(s % 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m`;
  return `${r}s`;
}

export function formatSize(bytes) {
  if (!bytes) return '—';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  let v = bytes;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(v >= 100 || i === 0 ? 0 : 1)} ${units[i]}`;
}