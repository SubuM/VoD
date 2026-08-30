import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getMovie, saveProgress, streamUrl } from '../api'

const SPEEDS = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2]

function fmt(sec) {
  if (!Number.isFinite(sec) || sec < 0) return '0:00'
  const s = Math.floor(sec)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const r = Math.floor(s % 60)
  const mm = h > 0 ? String(m).padStart(2, '0') : String(m)
  const ss = String(r).padStart(2, '0')
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`
}

export default function Watch() {
  const { id } = useParams()
  const navigate = useNavigate()
  const videoRef = useRef(null)
  const hideTimerRef = useRef(null)
  const saveTimerRef = useRef(null)
  const [movie, setMovie] = useState(null)
  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [duration, setDuration] = useState(0)
  const [volume, setVolume] = useState(1)
  const [muted, setMuted] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [speedOpen, setSpeedOpen] = useState(false)
  const [controlsVisible, setControlsVisible] = useState(true)
  const [ready, setReady] = useState(false)
  const [endScreen, setEndScreen] = useState(false)

  useEffect(() => {
    getMovie(id).then(setMovie).catch(() => setMovie(null))
  }, [id])

  // ---- resume from saved progress ----
  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    const onLoaded = () => {
      video.play()
        .then(() => {
          if (!movie?.progress_sec || movie.progress_sec < 3) return
          video.currentTime = Math.min(movie.progress_sec, video.duration - 2)
        })
        .catch(() => {})
    }
    video.addEventListener('loadedmetadata', onLoaded)
    return () => video.removeEventListener('loadedmetadata', onLoaded)
  }, [movie])

  // ---- periodic progress save ----
  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    clearInterval(saveTimerRef.current)
    saveTimerRef.current = setInterval(() => {
      if (!Number.isFinite(video.currentTime)) return
      saveProgress(id, video.currentTime, video.duration || movie?.duration_sec).catch(() => {})
    }, 5000)
    return () => clearInterval(saveTimerRef.current)
  }, [id, movie])

  const flushProgress = useCallback(() => {
    const video = videoRef.current
    if (video && Number.isFinite(video.currentTime) && video.currentTime > 1) {
      saveProgress(id, video.currentTime, video.duration || movie?.duration_sec).catch(() => {})
    }
  }, [id, movie])

  useEffect(() => () => flushProgress(), [flushProgress])

  // ---- controls auto-hide ----
  const pokeControls = useCallback(() => {
    setControlsVisible(true)
    clearTimeout(hideTimerRef.current)
    hideTimerRef.current = setTimeout(() => {
      setControlsVisible(false)
      setSpeedOpen(false)
    }, 2600)
  }, [])

  const togglePlay = useCallback(() => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) {
      video.play().catch(() => {})
    } else {
      video.pause()
    }
    pokeControls()
  }, [pokeControls])

  const skip = useCallback((delta) => {
    const video = videoRef.current
    if (!video) return
    video.currentTime = Math.max(0, Math.min(video.duration || 0, video.currentTime + delta))
    pokeControls()
  }, [pokeControls])

  const seekTo = useCallback((e) => {
    const video = videoRef.current
    if (!video || !video.duration) return
    const pct = Number(e.target.value)
    video.currentTime = (pct / 100) * video.duration
    setCurrent(video.currentTime)
    pokeControls()
  }, [pokeControls])

  const toggleMute = useCallback(() => {
    const video = videoRef.current
    if (!video) return
    if (video.muted) {
      video.muted = false
      setMuted(false)
    } else {
      video.muted = true
      setMuted(true)
    }
    pokeControls()
  }, [pokeControls])

  const setVol = useCallback((v) => {
    const video = videoRef.current
    if (!video) return
    video.volume = Number(v)
    setVolume(Number(v))
    setMuted(v === 0)
    pokeControls()
  }, [pokeControls])

  const setSpeedVol = useCallback((s) => {
    const video = videoRef.current
    if (video) video.playbackRate = s
    setSpeed(s)
    setSpeedOpen(false)
  }, [])

  const toggleFullscreen = useCallback(() => {
    const shell = document.querySelector('.player-shell')
    if (!shell) return
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {})
    } else {
      shell.requestFullscreen().catch(() => {})
    }
    pokeControls()
  }, [pokeControls])

  // ---- keyboard ----
  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT') return
      switch (e.key) {
        case ' ':
          e.preventDefault()
          togglePlay()
          break
        case 'ArrowLeft':
          skip(-10)
          break
        case 'ArrowRight':
          skip(10)
          break
        case 'ArrowUp':
          setVol(Math.min(1, (videoRef.current?.volume ?? 0) + 0.1))
          break
        case 'ArrowDown':
          setVol(Math.max(0, (videoRef.current?.volume ?? 0) - 0.1))
          break
        case 'm':
        case 'M':
          toggleMute()
          break
        case 'f':
        case 'F':
          toggleFullscreen()
          break
        case 'Escape':
          if (speedOpen) setSpeedOpen(false)
          break
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [togglePlay, skip, setVol, toggleMute, toggleFullscreen, speedOpen])

  if (!ready && !movie) {
    return (
      <div className="player-page">
        <div className="loading">
          <div className="spinner" />
        </div>
      </div>
    )
  }

  const pct = duration ? (current / duration) * 100 : 0
  const remaining = movie?.duration_sec ?? duration
  const ending = Number.isFinite(current) && Number.isFinite(remaining) && remaining - current <= 15

  return (
    <div className="player-page">
      <div
        className={`player-shell ${controlsVisible ? 'controls-visible' : ''} ${playing ? '' : 'paused'}`}
        onMouseMove={pokeControls}
        onClick={togglePlay}
      >
        <video
          ref={videoRef}
          className="player-video"
          src={streamUrl(id)}
          playsInline
          onClick={(e) => e.stopPropagation()}
          onPlay={() => {
            setPlaying(true)
            setEndScreen(false)
            pokeControls()
          }}
          onPause={() => setPlaying(false)}
          onWaiting={() => setPlaying(false)}
          onTimeUpdate={(e) => {
            setCurrent(e.target.currentTime)
            if (e.target.duration && e.target.currentTime >= e.target.duration - 2) setEndScreen(true)
          }}
          onDurationChange={(e) => setDuration(e.target.duration || 0)}
          onVolumeChange={(e) => setMuted(e.target.muted)}
          onEnded={() => {
            setPlaying(false)
            setEndScreen(true)
            flushProgress()
          }}
        />

        <div className="player-topbar">
          <button className="back-btn" aria-label="Back" onClick={(e) => { e.stopPropagation(); flushProgress(); navigate(-1) }}>
            ←
          </button>
          <span>{movie?.title}</span>
        </div>

        {speedOpen && (
          <div className="speed-menu" onClick={(e) => e.stopPropagation()}>
            {SPEEDS.map((s) => (
              <button key={s} className={s === speed ? 'active' : ''} onClick={() => setSpeedVol(s)}>
                {s}×
              </button>
            ))}
          </div>
        )}

        <div className="player-controls" onClick={(e) => e.stopPropagation()}>
          <div className="player-timeline">
            <span>{fmt(current)}</span>
            <input className="seek" type="range" min="0" max="100" step="0.01" value={pct || 0}
              style={{ '--progress': `${pct}%` }} onChange={seekTo} aria-label="Seek" />
            <span>{fmt(duration || remaining)}</span>
          </div>
          <div className="controls-row">
            <button className="play-pause" aria-label={playing ? 'Pause' : 'Play'} onClick={togglePlay}>
              {playing ? '❚❚' : '▶'}
            </button>
            <button className="icon-btn" aria-label="Skip back 10s" onClick={() => skip(-10)}>⟲10</button>
            <button className="icon-btn" aria-label="Skip forward 10s" onClick={() => skip(10)}>⏩10</button>
            <button className="icon-btn" style={{ width: 'auto', padding: '0 8px', fontSize: 14 }} onClick={toggleMute} aria-label="Mute">
              {muted || volume === 0 ? '🔇' : volume < 0.5 ? '🔉' : '🔊'}
            </button>
            <input className="vol" type="range" min="0" max="1" step="0.05" value={muted ? 0 : volume}
              onChange={(e) => setVol(e.target.value)} aria-label="Volume" />
            <div className="controls-spacer" />
            <button className="icon-btn" aria-label="Playback speed" onClick={() => setSpeedOpen((v) => !v)}>
              {speed}×
            </button>
            <button className="icon-btn" aria-label="Fullscreen" onClick={toggleFullscreen}>⛶</button>
          </div>
        </div>

        {ending && !playing && (endScreen || controlsVisible) && !speedOpen && (
          <div style={{ position: 'absolute', bottom: 120, width: '100%', left: 0, textAlign: 'center', zIndex: 25 }}>
            <button className="btn btn-primary" style={{ fontSize: 16 }} onClick={togglePlay}>
              ▶ Replay from start
            </button>
          </div>
        )}
      </div>
    </div>
  )
}