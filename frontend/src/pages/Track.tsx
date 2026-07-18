import React, { useCallback, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, errorMessage } from '../api'
import type { TrackResult } from '../types'
import StatusTimeline from '../components/StatusTimeline'

const STEP_LABELS: Record<string, string> = {
  submitted: 'Submitted',
  assigned: 'Assigned',
  in_progress: 'In Progress',
  resolved: 'Resolved',
}

const WASTE_LABELS: Record<string, string> = {
  bin: 'Overflowing Bin',
  dumping: 'Illegal Dumping',
  construction: 'Construction Debris',
  biohazard: 'Biohazard',
}

function Track() {
  const { ticket: ticketParam } = useParams()
  const navigate = useNavigate()
  const [input, setInput] = useState(ticketParam ?? '')
  const [result, setResult] = useState<TrackResult | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const lookup = useCallback(async (ticket: string) => {
    if (!ticket.trim()) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const { data } = await api.get<TrackResult>(
        `/complaints/track/${encodeURIComponent(ticket.trim())}`,
      )
      setResult(data)
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (ticketParam) lookup(ticketParam)
  }, [ticketParam, lookup])

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <div className="bg-white rounded-xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-1">🔎 Track a Complaint</h2>
        <p className="text-gray-600 text-sm mb-5">
          Enter your ticket number to see where your report stands. No sign-in needed.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            navigate(`/track/${encodeURIComponent(input.trim())}`)
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g. CL-17844006395706"
            className="flex-1 border border-gray-300 rounded px-3 py-2 font-mono text-sm"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 text-white px-5 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '…' : 'Track'}
          </button>
        </form>
        {error && (
          <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2 mt-4">
            {error}
          </p>
        )}
      </div>

      {result && (
        <div className="bg-white rounded-xl shadow-lg p-8 space-y-5">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-mono font-bold text-lg text-gray-800">
              {result.ticket_number}
            </span>
            <span className="text-sm text-gray-500 capitalize">
              {result.status.replace('_', ' ')} ·{' '}
              {WASTE_LABELS[result.waste_type ?? ''] ?? 'Waste issue'} · severity{' '}
              {result.severity_score}
            </span>
            {result.verified && (
              <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold">
                ✅ AI-verified clean
              </span>
            )}
          </div>

          {result.ward && (
            <p className="text-sm text-blue-800 bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
              📍 {result.ward.name}
              {result.ward.ward_number != null && ` (Ward No. ${result.ward.ward_number})`}
            </p>
          )}

          <StatusTimeline
            steps={result.timeline.map((s) => ({
              label: STEP_LABELS[s.step] ?? s.step,
              at: s.at,
              reached: s.reached,
            }))}
            rejected={result.status === 'rejected'}
          />

          {(result.photo_url || result.after_photo_url) && (
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
                  Reported
                </p>
                {result.photo_url ? (
                  <img
                    src={result.photo_url}
                    alt="Reported waste"
                    className="rounded-lg h-36 w-full object-cover"
                  />
                ) : (
                  <div className="rounded-lg h-36 bg-gray-100" />
                )}
              </div>
              <div>
                <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
                  After cleanup
                </p>
                {result.after_photo_url ? (
                  <img
                    src={result.after_photo_url}
                    alt="After cleanup"
                    className="rounded-lg h-36 w-full object-cover ring-2 ring-emerald-400"
                  />
                ) : (
                  <div className="rounded-lg h-36 bg-gray-100 flex items-center justify-center text-gray-400 text-xs">
                    {result.status === 'resolved' ? 'No photo taken' : 'Pending cleanup'}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Track
