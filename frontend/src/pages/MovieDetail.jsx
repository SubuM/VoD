import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { clearProgress, formatDuration, formatSize, getMovie } from '../api'

export default function MovieDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [movie, setMovie] = useState(null)
  const [imgFailed, setImgFailed] = useState(false)
  const [bgFailed, setBgFailed] = useState(false)

  useEffect(() => {
    let alive = true
    getMovie(id).then((m) => alive && setMovie(m)).catch(() => alive && setMovie(null))
    return () => {
      alive = false
    }
  }, [id])

  if (!movie) {
    return (
      <div className="loading">
        <div className="spinner" />
      </div>
    )
  }

  const resume = movie.progress_sec
  const hasPlayed = resume !== null && resume > 5

  const specs = [
    ['Runtime', formatDuration(movie.duration_sec)],
    ['Year', movie.year ?? '—'],
    ['Resolution', movie.width && movie.height ? `${movie.width}×${movie.height}` : '—'],
    ['Video codec', movie.video_codec ?? '—'],
    ['Audio', [movie.audio_codec, movie.audio_channels].filter(Boolean).join(' · ') || '—'],
    ['Container', movie.container?.toUpperCase() ?? '—'],
    ['File size', formatSize(movie.size_bytes)],
    ['File', movie.file_name],
  ]

  return (
    <div>
      <div className="detail-hero">
        {movie.backdrop_url && !bgFailed ? (
          <img className="detail-backdrop" src={movie.backdrop_url} alt="" onError={() => setBgFailed(true)} />
        ) : (
          <div className="detail-backdrop-fallback" />
        )}
        <div className="detail-shade" />
        <div className="detail-content">
          <div className="detail-poster-wrap">
            {movie.poster_url && !imgFailed ? (
              <img src={movie.poster_url} alt={movie.title} onError={() => setImgFailed(true)} />
            ) : (
              <div className="poster-fallback">
                {movie.title.split(/\s+/).slice(0, 3).map((w) => w[0]).join(' ').toUpperCase()}
              </div>
            )}
          </div>
          <div className="detail-info">
            <h1>{movie.title}</h1>
            <div className="detail-meta-line">
              <span>{movie.year ?? '—'}</span>
              <span>·</span>
              <span>{formatDuration(movie.duration_sec)}</span>
              <span>·</span>
              <span>{movie.width}×{movie.height}</span>
            </div>
            <div className="detail-actions">
              <button className="btn btn-primary" onClick={() => navigate(`/watch/${movie.id}`)}>
                ▶ {hasPlayed ? 'Resume playback' : 'Play'}
              </button>
              {hasPlayed && (
                <button
                  className="btn btn-ghost"
                  onClick={async () => {
                    await clearProgress(movie.id)
                    setMovie({ ...movie, progress_sec: 0, has_progress: false })
                  }}
                >
                  Restart from beginning
                </button>
              )}
            </div>
            {hasPlayed && (
              <p className="resume-hint" style={{ marginTop: 12 }}>
                Paused at {formatDuration(resume)} of {formatDuration(movie.duration_sec)}
              </p>
            )}
          </div>
        </div>
      </div>

      <dl className="spec-grid">
        {specs.map(([label, value]) => (
          <div className="spec-card" key={label}>
            <dt>{label}</dt>
            <dd title={value}>{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}