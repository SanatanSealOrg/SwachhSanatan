import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../store'

function Dashboard() {
  const navigate = useNavigate()
  const { userType } = useAuth()

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome back to Nagar Seva</h2>
      <p className="text-gray-600 mb-6">
        Report waste issues, track resolution, and help keep your ward clean.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {userType !== 'officer' && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-6 rounded">
            <h3 className="text-lg font-bold text-blue-700 mb-2">📱 Report Issue</h3>
            <p className="text-gray-600 text-sm">
              Submit a photo of overflowing bins or illegal dumping with your location.
            </p>
            <button
              onClick={() => navigate('/report')}
              className="mt-4 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Report Now
            </button>
          </div>
        )}

        {userType !== 'citizen' && (
          <div className="bg-purple-50 border-l-4 border-purple-500 p-6 rounded">
            <h3 className="text-lg font-bold text-purple-700 mb-2">👮 Officer Dashboard</h3>
            <p className="text-gray-600 text-sm">
              View prioritized tasks, assign to crews, and track resolution status.
            </p>
            <button
              onClick={() => navigate('/officer')}
              className="mt-4 bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
            >
              Go to Dashboard
            </button>
          </div>
        )}

        <div className="bg-green-50 border-l-4 border-green-500 p-6 rounded">
          <h3 className="text-lg font-bold text-green-700 mb-2">📊 Public Metrics</h3>
          <p className="text-gray-600 text-sm">
            View ward-by-ward cleanliness scores and complaint trends.
          </p>
          <button
            onClick={() => navigate('/metrics')}
            className="mt-4 bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
          >
            View Dashboard
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
