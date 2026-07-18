import React from 'react'
import type { QueueItem } from '../../types'

export const BAND_STYLES: Record<string, string> = {
  critical: 'bg-red-600 text-white',
  high: 'bg-orange-500 text-white',
  medium: 'bg-yellow-400 text-gray-900',
  low: 'bg-gray-200 text-gray-600',
}

const WASTE_LABELS: Record<string, string> = {
  bin: 'Overflowing Bin',
  dumping: 'Illegal Dumping',
  construction: 'Construction Debris',
  biohazard: 'Biohazard',
}

interface Props {
  items: QueueItem[]
  busyId: string | null
  onStart: (item: QueueItem) => void
  onResolve: (item: QueueItem) => void
}

function PriorityQueue({ items, busyId, onStart, onResolve }: Props) {
  if (items.length === 0) {
    return (
      <p className="text-gray-500 bg-white rounded-xl shadow p-6 text-center">
        🎉 No active complaints match — your ward queue is clear.
      </p>
    )
  }
  return (
    <div className="space-y-3">
      {items.map((c) => (
        <div
          key={c.id}
          className={`bg-white rounded-xl shadow p-4 flex gap-4 ${
            c.age_bucket === 'overdue' ? 'border-l-4 border-red-500' : ''
          }`}
        >
          {c.image_urls[0] ? (
            <img
              src={c.image_urls[0]}
              alt="Complaint"
              className="w-20 h-20 rounded-lg object-cover shrink-0"
            />
          ) : (
            <div className="w-20 h-20 rounded-lg bg-gray-100 flex items-center justify-center text-2xl shrink-0">
              🗑️
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${BAND_STYLES[c.priority_band]}`}
              >
                {c.priority_band}
              </span>
              <span className="font-mono text-sm font-semibold text-gray-700">
                {c.ticket_number}
              </span>
              <span className="text-xs text-gray-400">
                score {c.priority_score}
              </span>
              {c.age_bucket === 'overdue' && <span title="Overdue">🚩</span>}
            </div>
            <p className="text-sm text-gray-700 mt-1 truncate">
              {WASTE_LABELS[c.waste_type ?? ''] ?? 'Waste issue'} — {c.description}
            </p>
            <div className="flex flex-wrap gap-1 mt-1.5">
              {c.reasons.map((r) => (
                <span
                  key={r}
                  className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
                >
                  {r}
                </span>
              ))}
            </div>
          </div>
          <div className="flex flex-col gap-2 justify-center shrink-0">
            {(c.status === 'open' || c.status === 'assigned') && (
              <button
                type="button"
                disabled={busyId === c.id}
                onClick={() => onStart(c)}
                className="text-sm bg-blue-600 text-white px-4 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                Start
              </button>
            )}
            {c.status === 'in_progress' && (
              <button
                type="button"
                disabled={busyId === c.id}
                onClick={() => onResolve(c)}
                className="text-sm bg-green-600 text-white px-4 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50"
              >
                Resolve ✓
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default PriorityQueue
