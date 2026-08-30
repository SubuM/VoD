import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getMovies } from '../api'
import MovieCard from '../components/MovieCard'

export default function Browse() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  const [sort, setSort] = useState('added')
  const [movies, setMovies] = useState(null)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    let alive = true
    getMovies({ search: q || undefined, sort, page_size: 100 })
      .then((page) => {
        if (!alive) return
        setMovies(page.items)
        setTotal(page.total)
      })
      .catch(() => alive && setMovies([]))
    return () => {
      alive = false
    }
  }, [q, sort])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 14, marginBottom: 20 }}>
        <h1 className="section-title" style={{ fontSize: 24, margin: 0 }}>
          {q ? `Results for “${q}”` : 'All movies'}
        </h1>
        <span className="text-dim">{total} found</span>
        <div style={{ marginLeft: 'auto' }}>
          <label className="sr-only" htmlFor="sort">Sort</label>
          <select
            id="sort"
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            style={{
              background: 'var(--bg-card)',
              color: 'var(--text)',
              border: '1px solid var(--border)',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 13.5,
            }}
          >
            <option value="added">Recently added</option>
            <option value="title">Title A–Z</option>
            <option value="year">Year</option>
            <option value="random">Random</option>
          </select>
        </div>
      </div>

      {!movies ? (
        <div className="loading">
          <div className="spinner" />
        </div>
      ) : movies.length === 0 ? (
        <div className="empty">
          <h2>Nothing found</h2>
          <p>Try a different title or year.</p>
        </div>
      ) : (
        <div className="grid">{movies.map((m) => <MovieCard key={m.id} movie={m} />)}</div>
      )}
    </div>
  )
}