import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../api'
import type { MyComplaint } from '../types'
import StatusTimeline, { buildSteps } from '../components/StatusTimeline'
import CelebrationOverlay from '../components/CelebrationOverlay'

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-red-100 text-red-700',
  assigned: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  rejected: 'bg-gray-200 text-gray-600',
}

const WASTE_LABELS: Record<string, string> = {
  bin: 'Overflowing Bin',
  dumping: 'Illegal Dumping',
  construction: 'Construction Debris',
  biohazard: 'Biohazard',
}

function MyComplaints() {
  const [complaints, setComplaints] = useState<MyComplaint[]>([])
  const [impact, setImpact] = useState<MyComplaint | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/complaints/mine')
      .then(({ data }) => setComplaints(data.complaints))
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  const resolvedCount = complaints.filter((c) => c.status === 'resolved').length

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-1">🗂️ My Reports</h2>
        <p className="text-gray-600 text-sm">
          Every report you make helps keep Chennai clean.
          {resolvedCount > 0 && (
            <>
              {' '}
              <span className="font-semibold text-emerald-700">
                {resolvedCount} of your reports already led to a cleanup 💚
              </span>
            </>
          )}
        </p>
      </div>

      {error && (
        <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-gray-500">Loading your reports…</p>
      ) : complaints.length === 0 ? (
        <div className="bg-white rounded-xl shadow p-8 text-center text-gray-500">
          <p className="mb-3">You haven't reported anything yet.</p>
          <Link
            to="/report"
            className="inline-block bg-green-600 text-white px-5 py-2 rounded-lg hover:bg-green-700"
          >
            📱 Report your first issue
          </Link>
        </div>
      ) : (
        complaints.map((c) => {
          const resolved = c.status === 'resolved'
          const afterUrl = c.assignment?.completion_image_url ?? null
          return (
            <div key={c.id} className="bg-white rounded-xl shadow p-5 space-y-4">
              <div className="flex items-center gap-3 flex-wrap">
                <span className="font-mono font-bold text-gray-800">{c.ticket_number}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full font-semibold capitalize ${STATUS_COLORS[c.status] ?? ''}`}
                >
                  {c.status.replace('_', ' ')}
                </span>
                <span className="text-xs text-gray-500">
                  {WASTE_LABELS[c.waste_type ?? ''] ?? 'Waste issue'}
                  {c.ward_name && ` · ${c.ward_name}`}
                </span>
                {c.assignment?.verified && (
                  <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold">
                    ✅ Verified clean
                  </span>
                )}
              </div>

              <StatusTimeline
                steps={buildSteps(
                  c.status,
                  c.created_at,
                  c.assignment?.assigned_at ?? null,
                  c.resolved_at,
                )}
                rejected={c.status === 'rejected'}
              />

              <div className="flex gap-3 items-start">
                {c.image_urls[0] && (
                  <img
                    src={c.image_urls[0]}
                    alt="Report"
                    className="w-24 h-24 rounded-lg object-cover"
                  />
                )}
                {afterUrl && (
                  <img
                    src={afterUrl}
                    alt="After cleanup"
                    className="w-24 h-24 rounded-lg object-cover ring-2 ring-emerald-400"
                  />
                )}
                <p className="text-sm text-gray-600 flex-1">{c.description}</p>
              </div>

              {resolved && (
                <button
                  type="button"
                  onClick={() => setImpact(c)}
                  className="w-full bg-gradient-to-r from-emerald-500 to-green-600 text-white py-2 rounded-lg font-semibold hover:from-emerald-600 hover:to-green-700"
                >
                  🎉 See your impact
                </button>
              )}
            </div>
          )
        })
      )}

      {impact && (
        <CelebrationOverlay
          role="citizen"
          wardName={impact.ward_name ?? ''}
          beforeUrl={impact.image_urls[0] ?? null}
          afterUrl={impact.assignment?.completion_image_url ?? null}
          verification={
            impact.assignment?.verified
              ? {
                  after_image_url: impact.assignment.completion_image_url ?? '',
                  ssim: impact.assignment.verification_ssim_score,
                  suspicious_similarity: false,
                  ai: { cleaned: true, confidence: 1, note: '', source: 'stored' },
                  verified: true,
                }
              : null
          }
          onClose={() => setImpact(null)}
        />
      )}
    </div>
  )
}

export default MyComplaints
