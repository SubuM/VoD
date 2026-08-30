import { useEffect, useState } from 'react'
import { getContinueWatching, getLibraryStatus, getMovies, rescan } from '../api'
import MovieRow from '../components/MovieRow'

function Loading() {
  return (
    <div className="loading">
      <div className="spinner" />
      Scanning your library…
    </div>
  )
}

function EmptyLibrary({ status }) {
  return (
    <div className="empty">
      <h2>Your library is empty</h2>
      <p>
        Point this app at a folder full of movies by setting <b>MEDIA_DIR</b> in{' '}
        <code>backend/.env</code> to your USB drive path (e.g.{' '}
        <code>/media/usb/movies</code>), then add your files and rescan.
      </p>
      <p className="text-dim" style={{ fontSize: '12.5px' }}>
        Currently configured to scan: {status?.media_dirs?.map((d) => <code key={d}>{d}</code>).join(', ')}
      </p>
      <button className="btn btn-primary" onClick={() => rescan(true)}>
        Rescan now
      </button>
    </div>
  )
}

export default function Home() {
  const [movies, setMovies] = useState(null)
  const [continueWatching, setContinueWatching] = useState([])
  const [status, setStatus] = useState(null)

  useEffect(() => {
    let alive = true
    Promise.all([getMovies({ sort: 'added', page_size: 48 }), getContinueWatching(), getLibraryStatus()])
      .then(([moviePage, cw, lib]) => {
        if (!alive) return
        setMovies(moviePage.items)
        setContinueWatching(cw)
        setStatus(lib)
      })
      .catch(() => alive && setMovies([]))
    return () => {
      alive = false
    }
  }, [])

  if (movies === null) return <Loading />
  if (!status?.movie_count) return <EmptyLibrary status={status} />

  return (
    <>
      {continueWatching.length > 0 && (
        <MovieRow title="Continue watching" movies={continueWatching} />
      )}
      {movies.length > 0 && <MovieRow title="Recent additions" movies={movies} />}
    </>
  )
}