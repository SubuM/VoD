import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { formatDuration } from '../api'

function Fallback({ title }) {
  const initials = title
    .split(/\s+/)
    .filter((w) => w.length > 1 && /^[A-Za-z0-9]/.test(w))
    .slice(0, 3)
    .map((w) => w[0].toUpperCase())
    .join(' ') || '?'
  return <div className="poster-fallback">{initials}</div>
}

export default function MovieCard({ movie }) {
  const navigate = useNavigate()
  const [imgFailed, setImgFailed] = useState(false)
  const progress = movie.progress_sec ?? null
  const duration = movie.duration_sec ?? null
  const pct = progress !== null && duration ? Math.min(100, (progress / duration) * 100) : null

  return (
    <div
      className="movie-card"
      role="link"
      tabIndex={0}
      onClick={() => navigate(`/movie/${movie.id}`)}
      onKeyDown={(e) => e.key === 'Enter' && navigate(`/movie/${movie.id}`)}
    >
      <div className="poster-wrap">
        {movie.poster_url && !imgFailed ? (
          <img className="poster-img" src={movie.poster_url} alt={movie.title} loading="lazy" onError={() => setImgFailed(true)} />
        ) : (
          <Fallback title={movie.title} />
        )}
        {pct !== null && pct > 1 && (
          <>
            <span className="watch-again">▶ {formatDuration(progress)} left</span>
            <div className="card-progress">
              <div style={{ width: `${pct}%` }} />
            </div>
          </>
        )}
      </div>
      <div className="card-body">
        <p className="card-title" title={movie.title}>
          {movie.title}
        </p>
        <p className="card-meta">
          {movie.year ?? '—'} · {formatDuration(duration)}
        </p>
      </div>
    </div>
  )
}