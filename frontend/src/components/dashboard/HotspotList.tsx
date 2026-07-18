import React from 'react'
import type { Hotspot } from '../../types'

const WASTE_LABELS: Record<string, string> = {
  bin: 'Overflowing bins',
  dumping: 'Illegal dumping',
  construction: 'Construction debris',
  biohazard: 'Biohazard waste',
}

interface Props {
  hotspots: Hotspot[]
}

function HotspotList({ hotspots }: Props) {
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-gray-800">🔥 AI-Detected Hotspots</h3>
      {hotspots.length === 0 ? (
        <p className="text-sm text-gray-500">No active hotspots — the city is looking clean.</p>
      ) : (
        hotspots.map((h) => (
          <div
            key={h.id}
            className="border border-red-200 bg-red-50 rounded-lg p-3 text-sm"
          >
            <p className="font-semibold text-red-800">
              🔥 {h.count} reports · {WASTE_LABELS[h.dominant_waste_type ?? ''] ?? 'Mixed waste'}
            </p>
            <p className="text-red-700 text-xs mt-0.5">
              Avg severity {h.avg_severity} · radius ~{Math.round(h.radius_m)}m
              {h.last_reported &&
                ` · last report ${new Date(h.last_reported).toLocaleDateString()}`}
            </p>
          </div>
        ))
      )}
      <p className="text-[11px] text-gray-400">
        Hotspots are detected automatically by clustering active complaints (DBSCAN, last 30
        days).
      </p>
    </div>
  )
}

export default HotspotList
