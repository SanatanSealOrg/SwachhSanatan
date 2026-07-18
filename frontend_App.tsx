import React, { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-green-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-green-700">
            🗑️ CleanLoop
          </h1>
          <p className="text-gray-600 mt-2">Community Waste & Sanitation Intelligence</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome to CleanLoop</h2>
          <p className="text-gray-600 mb-6">
            Report waste issues, track resolution, and help keep your ward clean.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Citizen Report Card */}
            <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded">
              <h3 className="text-lg font-bold text-blue-700 mb-2">📱 Report Issue</h3>
              <p className="text-gray-600 text-sm">
                Submit a photo of overflowing bins or illegal dumping with your location.
              </p>
              <button className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                Report Now
              </button>
            </div>

            {/* Officer Dashboard Card */}
            <div className="bg-purple-50 border-l-4 border-purple-500 p-6 rounded">
              <h3 className="text-lg font-bold text-purple-700 mb-2">👮 Officer Dashboard</h3>
              <p className="text-gray-600 text-sm">
                View prioritized tasks, assign to crews, and track resolution status.
              </p>
              <button className="mt-4 bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600">
                Go to Dashboard
              </button>
            </div>

            {/* Public Dashboard Card */}
            <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded">
              <h3 className="text-lg font-bold text-green-700 mb-2">📊 Public Metrics</h3>
              <p className="text-gray-600 text-sm">
                View ward-by-ward cleanliness scores and complaint trends.
              </p>
              <button className="mt-4 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                View Dashboard
              </button>
            </div>
          </div>

          {/* Dev Counter */}
          <div className="mt-12 p-4 bg-gray-100 rounded text-center">
            <p className="text-sm text-gray-500">React Component Test Counter:</p>
            <button
              onClick={() => setCount(count + 1)}
              className="mt-2 bg-gray-800 text-white px-6 py-2 rounded hover:bg-gray-700"
            >
              Count is: {count}
            </button>
          </div>
        </div>

        {/* Status Indicator */}
        <div className="mt-8 bg-green-100 border border-green-300 rounded p-4 text-center">
          <p className="text-green-700 font-semibold">✅ Frontend is running</p>
        </div>
      </main>

      <footer className="bg-gray-800 text-white mt-12">
        <div className="max-w-7xl mx-auto px-4 py-6 text-center">
          <p>CleanLoop v0.1.0 | Community Waste Intelligence Platform for Chennai</p>
        </div>
      </footer>
    </div>
  )
}

export default App
