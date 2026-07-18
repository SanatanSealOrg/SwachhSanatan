import React, { useCallback, useEffect, useState } from 'react'
import { api, errorMessage } from '../api'
import { useAuth } from '../store'
import OfficerDashboard from '../components/officer/OfficerDashboard'

interface Complaint {
  id: string
  ticket_number: string
  status: string
  description: string | null
  waste_type: string | null
  severity_score: number
  image_urls: string[]
  created_at: string | null
}

interface WardInfo {
  id: string
  name: string
  ward_number: number | null
}

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-red-100 text-red-700',
  assigned: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  rejected: 'bg-gray-200 text-gray-600',
}

function Officer() {
  const { wardId, userType } = useAuth()

  // Officers get the rich command center; admins/others keep the ward browser below
  if (userType === 'officer') {
    return <OfficerDashboard />
  }
  return <LegacyOfficerTable wardId={wardId} userType={userType} />
}

function LegacyOfficerTable({
  wardId,
  userType,
}: {
  wardId: string | null
  userType: string | null
}) {
  const [wards, setWards] = useState<WardInfo[]>([])
  const [selectedWard, setSelectedWard] = useState<string>(wardId ?? '')
  const [statusFilter, setStatusFilter] = useState('')
  const [complaints, setComplaints] = useState<Complaint[]>([])
  const [total, setTotal] = useState(0)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    api
      .get('/wards')
      .then(({ data }) => {
        setWards(data.wards)
        // Officers are locked to their own ward; others default to the first ward
        if (!wardId && !selectedWard && data.wards.length > 0) {
          setSelectedWard(data.wards[0].id)
        }
      })
      .catch((err) => setError(errorMessage(err)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const load = useCallback(() => {
    if (!selectedWard) return
    setLoading(true)
    setError('')
    const params: Record<string, string> = { ward_id: selectedWard }
    if (statusFilter) params.status = statusFilter
    api
      .get('/complaints', { params })
      .then(({ data }) => {
        setComplaints(data.complaints)
        setTotal(data.total)
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [selectedWard, statusFilter])

  useEffect(load, [load])

  const updateStatus = async (id: string, status: string) => {
    try {
      await api.patch(`/complaints/${id}`, { status })
      load()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">👮 Officer Dashboard</h2>

      <div className="flex flex-wrap gap-4 mb-6">
        <div>
          <label htmlFor="ward-select" className="block text-sm font-medium text-gray-700 mb-1">
            Ward
          </label>
          <select
            id="ward-select"
            value={selectedWard}
            onChange={(e) => setSelectedWard(e.target.value)}
            disabled={userType === 'officer'}
            className="border border-gray-300 rounded px-3 py-2 disabled:bg-gray-100"
          >
            {wards.map((w) => (
              <option key={w.id} value={w.id}>
                {w.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="status-filter" className="block text-sm font-medium text-gray-700 mb-1">
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2"
          >
            <option value="">All</option>
            <option value="open">Open</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
        <div className="self-end text-sm text-gray-500">{total} complaint(s)</div>
      </div>

      {error && (
        <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2 mb-4">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-gray-500">Loading…</p>
      ) : complaints.length === 0 ? (
        <p className="text-gray-500">No complaints found for this ward.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2 pr-4">Ticket</th>
                <th className="py-2 pr-4">Description</th>
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Severity</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Created</th>
                <th className="py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {complaints.map((c) => (
                <tr key={c.id} className="border-b last:border-0">
                  <td className="py-2 pr-4 font-mono">{c.ticket_number}</td>
                  <td className="py-2 pr-4 max-w-xs truncate">{c.description}</td>
                  <td className="py-2 pr-4">{c.waste_type ?? '—'}</td>
                  <td className="py-2 pr-4">{c.severity_score}</td>
                  <td className="py-2 pr-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${STATUS_COLORS[c.status] ?? ''}`}>
                      {c.status}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    {c.created_at ? new Date(c.created_at).toLocaleString() : '—'}
                  </td>
                  <td className="py-2 space-x-2 whitespace-nowrap">
                    {userType === 'officer' && c.status !== 'resolved' && (
                      <>
                        {(c.status === 'open' || c.status === 'assigned') && (
                          <button
                            onClick={() => updateStatus(c.id, 'in_progress')}
                            className="text-blue-700 hover:underline"
                          >
                            Start
                          </button>
                        )}
                        {c.status === 'in_progress' && (
                          <button
                            onClick={() => updateStatus(c.id, 'resolved')}
                            className="text-green-700 hover:underline"
                          >
                            Resolve
                          </button>
                        )}
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Officer
