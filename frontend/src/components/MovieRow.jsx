import MovieCard from './MovieCard'

export default function MovieRow({ title, movies, nowrap = true }) {
  if (!movies || movies.length === 0) return null
  return (
    <section className="section">
      <h2 className="section-title">{title}</h2>
      <div className={nowrap ? 'row row-nowrap' : 'row'}>{movies.map((m) => <MovieCard key={m.id} movie={m} />)}</div>
    </section>
  )
}