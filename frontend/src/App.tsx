import React from 'react'
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './store'
import Home from './pages/Home'
import Login from './pages/Login'
import Report from './pages/Report'
import Officer from './pages/Officer'
import Metrics from './pages/Metrics'

function RequireAuth({ children }: { children: React.ReactElement }) {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }
  return children
}

function Shell({ children }: { children: React.ReactNode }) {
  const { token, email, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100 flex flex-col">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8 flex items-center justify-between">
          <div>
            <Link to="/" className="text-4xl font-bold text-green-700">
              🗑️ CleanLoop
            </Link>
            <p className="text-gray-600 mt-2">Community Waste & Sanitation Intelligence</p>
          </div>
          <div className="text-sm text-right">
            {token ? (
              <>
                <p className="text-gray-600 mb-1">{email}</p>
                <button onClick={logout} className="text-red-600 hover:underline">
                  Sign out
                </button>
              </>
            ) : (
              <Link to="/login" className="text-green-700 font-medium hover:underline">
                Sign in
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl w-full mx-auto px-4 py-12 sm:px-6 lg:px-8 flex-1">
        {children}
      </main>

      <footer className="bg-gray-800 text-white mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center">
          <p>CleanLoop v0.1.0 | Community Waste Intelligence Platform for Chennai</p>
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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  )
}

export default App
