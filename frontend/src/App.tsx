import React from 'react'
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from './store'
import Home from './pages/Home'
import Login from './pages/Login'
import Report from './pages/Report'
import Officer from './pages/Officer'
import Metrics from './pages/Metrics'
import MyComplaints from './pages/MyComplaints'
import Track from './pages/Track'

function RequireAuth({ children }: { children: React.ReactElement }) {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  return children
}

function Shell({ children }: { children: React.ReactNode }) {
  const { token, email, userType, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const isLandingPage = location.pathname === '/' && !token

  const handleSignOut = () => {
    logout()
    navigate('/', { replace: true })
  }

  const navLinks = (
    <nav className="flex flex-wrap items-center gap-4">
      <Link to="/track" className="text-blue-700 hover:underline">
        🔎 Track
      </Link>
      {token && userType !== 'officer' && (
        <Link to="/my-complaints" className="text-blue-700 hover:underline">
          🗂️ My Reports
        </Link>
      )}
      {token && userType === 'officer' && (
        <Link to="/officer" className="text-blue-700 hover:underline">
          🛡️ Dashboard
        </Link>
      )}
    </nav>
  )

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 flex flex-col">
      <header className="bg-white shadow">
        {isLandingPage ? (
          <div className="max-w-7xl mx-auto px-4 py-3 sm:px-6 lg:px-8 flex justify-end items-center gap-4 text-sm">
            {navLinks}
            <Link to="/login" className="text-green-700 font-medium hover:underline">
              Sign in
            </Link>
          </div>
        ) : (
          <div className="max-w-7xl mx-auto px-4 py-4 sm:py-6 sm:px-6 lg:px-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <Link to="/" className="text-2xl sm:text-4xl font-bold text-green-700">
                🧹 Nagar Seva
              </Link>
              <p className="text-gray-600 mt-1 text-sm sm:text-base">
                Community Waste &amp; Sanitation Intelligence
              </p>
            </div>
            <div className="flex flex-col gap-2 text-sm sm:items-end">
              {navLinks}
              {token ? (
                <div className="flex items-center gap-3">
                  <p className="text-gray-600 truncate max-w-[180px]">{email}</p>
                  <button onClick={handleSignOut} className="text-red-600 hover:underline shrink-0">
                    Sign out
                  </button>
                </div>
              ) : (
                <Link to="/login" className="text-green-700 font-medium hover:underline">
                  Sign in
                </Link>
              )}
            </div>
          </div>
        )}
      </header>

      <main
        className={`max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex-1 ${
          isLandingPage ? 'py-4 sm:py-6' : 'py-12'
        }`}
      >
        {children}
      </main>

      <footer className="bg-gray-800 text-white mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center">
          <p>Nagar Seva v0.1.0 | Community Waste Intelligence Platform for Chennai</p>
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Shell>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/report"
            element={
              <RequireAuth>
                <Report />
              </RequireAuth>
            }
          />
          <Route
            path="/officer"
            element={
              <RequireAuth>
                <Officer />
              </RequireAuth>
            }
          />
          <Route path="/metrics" element={<Metrics />} />
          <Route
            path="/my-complaints"
            element={
              <RequireAuth>
                <MyComplaints />
              </RequireAuth>
            }
          />
          <Route path="/track" element={<Track />} />
          <Route path="/track/:ticket" element={<Track />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  )
}

export default App
