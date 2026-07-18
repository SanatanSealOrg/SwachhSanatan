import React from 'react'
import type { WardMetric } from '../../types'

const BAND_TEXT: Record<string, string> = {
  green: 'text-emerald-600 border-emerald-500',
  yellow: 'text-amber-600 border-amber-500',
  red: 'text-red-600 border-red-500',
}

interface Props {
  metrics: WardMetric[]
}

function WardRanking({ metrics }: Props) {
  const ranked = [...metrics].sort((a, b) => b.cleanliness_score - a.cleanliness_score)

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-gray-800">🏆 Ward Cleanliness Ranking</h3>
      {ranked.map((m, i) => (
        <div
          key={m.ward_id}
          className="border rounded-lg p-3 flex items-center gap-3 bg-white hover:shadow-sm transition-shadow"
        >
          <span
            className={`w-7 h-7 flex items-center justify-center rounded-full text-xs font-bold ${
              i === 0
                ? 'bg-yellow-400 text-white'
                : i === 1
                  ? 'bg-gray-300 text-gray-700'
                  : i === 2
                    ? 'bg-amber-600 text-white'
                    : 'bg-gray-100 text-gray-500'
            }`}
          >
            {i + 1}
          </span>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-800 truncate">{m.ward_name}</p>
            <p className="text-xs text-gray-500">
              {m.open} open · {m.resolved} resolved
              {m.avg_resolution_hours != null && ` · avg ${Math.round(m.avg_resolution_hours)}h`}
            </p>
            {m.resolution_rate != null && (
              <div className="mt-1 h-1.5 bg-gray-200 rounded overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${m.resolution_rate}%` }}
                />
              </div>
            )}
          </div>
          <span
            className={`w-12 h-12 flex flex-col items-center justify-center rounded-full border-[3px] shrink-0 ${BAND_TEXT[m.band]}`}
          >
            <span className="text-sm font-bold leading-none">
              {Math.round(m.cleanliness_score)}
            </span>
            <span className="text-[8px] uppercase">score</span>
          </span>
        </div>
      ))}
    </div>
  )
}

export default WardRanking
