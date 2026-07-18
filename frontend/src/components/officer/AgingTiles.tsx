import React from 'react'

export type AgeBucket = 'fresh' | 'aging' | 'overdue'

const TILES: { key: AgeBucket; label: string; icon: string; accent: string; active: string }[] = [
  { key: 'fresh', label: 'Fresh (< 2 days)', icon: '🟢', accent: 'text-emerald-600', active: 'ring-2 ring-emerald-500' },
  { key: 'aging', label: 'Aging (2–7 days)', icon: '🟠', accent: 'text-amber-600', active: 'ring-2 ring-amber-500' },
  { key: 'overdue', label: 'Overdue (> 7 days)', icon: '🔴', accent: 'text-red-600', active: 'ring-2 ring-red-500' },
]

interface Props {
  counts: { fresh: number; aging: number; overdue: number; total: number }
  selected: AgeBucket | null
  onSelect: (bucket: AgeBucket | null) => void
}

function AgingTiles({ counts, selected, onSelect }: Props) {
  return (
    <div className="grid grid-cols-3 gap-3">
      {TILES.map((t) => (
        <button
          key={t.key}
          type="button"
          onClick={() => onSelect(selected === t.key ? null : t.key)}
          className={`bg-white rounded-xl shadow p-4 text-left transition-shadow hover:shadow-md ${
            selected === t.key ? t.active : ''
          } ${t.key === 'overdue' && counts.overdue > 0 ? 'animate-pulse' : ''}`}
        >
          <p className={`text-2xl font-bold ${t.accent}`}>
            {t.icon} {counts[t.key]}
          </p>
          <p className="text-xs text-gray-500 mt-1">{t.label}</p>
        </button>
      ))}
    </div>
  )
}

export default AgingTiles
