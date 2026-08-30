import { Route, Routes, useLocation } from 'react-router-dom'
import Header from './components/Header'
import Home from './pages/Home'
import Browse from './pages/Browse'
import MovieDetail from './pages/MovieDetail'
import Watch from './pages/Watch'

export default function App() {
  const location = useLocation()
  const isPlayer = location.pathname.startsWith('/watch/')

  return (
    <div className="app">
      {!isPlayer && <Header />}
      <main className={isPlayer ? '' : 'main'}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/browse" element={<Browse />} />
          <Route path="/movie/:id" element={<MovieDetail />} />
          <Route path="/watch/:id" element={<Watch />} />
        </Routes>
      </main>
    </div>
  )
}