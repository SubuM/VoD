import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getLibraryStatus } from '../api'

export default function Header() {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [count, setCount] = useState(null)
  const timer = useRef(null)

  useEffect(() => {
    getLibraryStatus()
      .then((s) => setCount(s.movie_count))
      .catch(() => {})
  }, [])

  function goSearch(e) {
    e.preventDefault()
    const term = q.trim()
    if (term) navigate(`/browse?q=${encodeURIComponent(term)}`)
  }

  function onChange(e) {
    setQ(e.target.value)
    clearTimeout(timer.current)
    const term = e.target.value.trim()
    if (!term) return
    timer.current = setTimeout(() => navigate(`/browse?q=${encodeURIComponent(term)}`), 450)
  }

  return (
    <header className="header">
      <a className="brand" href="/">
        <span className="brand-badge">F</span>
        FlashView
      </a>
      <form className="search-form" onSubmit={goSearch}>
        <svg
          className="search-icon"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          viewBox="0 0 24 24"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" strokeLinecap="round" />
        </svg>
        <input
          className="search-input"
          type="search"
          placeholder="Search your library…"
          value={q}
          onChange={onChange}
        />
      </form>
      <div className="header-right">
        <span className="movie-count">{count === null ? '…' : `${count} movies`}</span>
      </div>
    </header>
  )
}