import React, { useState } from 'react'
import type { AiDraft } from '../types'

const WASTE_TYPES = [
  { value: 'bin', label: 'Overflowing Bin' },
  { value: 'dumping', label: 'Illegal Dumping' },
  { value: 'construction', label: 'Construction Debris' },
  { value: 'biohazard', label: 'Biohazard' },
]

const SEVERITY_LABELS = ['', 'Minor', 'Low', 'Moderate', 'High', 'Urgent']

export interface DraftFields {
  title: string
  description: string
  wasteType: string
  severity: number
}

interface Props {
  previewUrl: string | null
  draft: AiDraft | null
  busy: boolean
  error: string
  onSubmit: (fields: DraftFields) => void
  onBack: () => void
}

function AiBadge({ visible }: { visible: boolean }) {
  if (!visible) return null
  return (
    <span className="ml-2 inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
      ✨ AI suggested
    </span>
  )
}

function AiDraftForm({ previewUrl, draft, busy, error, onSubmit, onBack }: Props) {
  const aiMode = draft !== null
  const [title, setTitle] = useState(draft?.title ?? '')
  const [description, setDescription] = useState(draft?.description ?? '')
  const [wasteType, setWasteType] = useState(draft?.waste_type ?? 'bin')
  const [severity, setSeverity] = useState(draft?.severity ?? 3)
  const [touched, setTouched] = useState<Set<string>>(new Set())

  const touch = (field: string) =>
    setTouched((prev) => {
      const next = new Set(prev)
      next.add(field)
      return next
    })

  const suggested = (field: string) => aiMode && !touched.has(field)

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onSubmit({ title, description, wasteType, severity })
      }}
      className="space-y-5"
    >
      {aiMode && (
        <div className="flex items-start gap-3 bg-emerald-50 border border-emerald-200 rounded-lg p-3">
          <span className="text-xl">🤖</span>
          <div className="text-sm">
            <p className="font-semibold text-emerald-800">AI drafted this complaint for you</p>
            <p className="text-emerald-700">
              Review the details below — everything is editable before you submit.
            </p>
            {draft.source === 'mock' && (
              <p className="text-xs text-emerald-600 mt-1 italic">
                Draft generated offline (demo mode)
              </p>
            )}
          </div>
        </div>
      )}

      {previewUrl && (
        <img
          src={previewUrl}
          alt="Waste report"
          className="w-full max-h-72 object-cover rounded-xl shadow-md"
        />
      )}

      {aiMode && (
        <div>
          <div className="flex justify-between text-xs text-gray-500 mb-1">
            <span>AI confidence</span>
            <span className="font-semibold text-gray-700">
              {Math.round(draft.confidence * 100)}%
            </span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${draft.confidence >= 0.7 ? 'bg-emerald-500' : draft.confidence >= 0.4 ? 'bg-amber-400' : 'bg-red-400'}`}
              style={{ width: `${Math.round(draft.confidence * 100)}%` }}
            />
          </div>
        </div>
      )}

      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
          Title
          <AiBadge visible={suggested('title')} />
        </label>
        <input
          id="title"
          value={title}
          onChange={(e) => {
            setTitle(e.target.value)
            touch('title')
          }}
          placeholder="Short summary of the issue"
          className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Official description
          <AiBadge visible={suggested('description')} />
        </label>
        <textarea
          id="description"
          required
          rows={5}
          value={description}
          onChange={(e) => {
            setDescription(e.target.value)
            touch('description')
          }}
          placeholder="e.g. Overflowing bin at the street corner"
          className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>

      <div>
        <label htmlFor="waste-type" className="block text-sm font-medium text-gray-700 mb-1">
          Waste Type
          <AiBadge visible={suggested('wasteType')} />
        </label>
        <select
          id="waste-type"
          value={wasteType}
          onChange={(e) => {
            setWasteType(e.target.value)
            touch('wasteType')
          }}
          className="w-full border border-gray-300 rounded px-3 py-2"
        >
          {WASTE_TYPES.map((w) => (
            <option key={w.value} value={w.value}>
              {w.label}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="severity" className="block text-sm font-medium text-gray-700 mb-1">
          Severity: {severity} — {SEVERITY_LABELS[severity]}
          <AiBadge visible={suggested('severity')} />
        </label>
        <input
          id="severity"
          type="range"
          min={1}
          max={5}
          value={severity}
          onChange={(e) => {
            setSeverity(Number(e.target.value))
            touch('severity')
          }}
          className="w-full accent-emerald-600"
        />
        {aiMode && draft.severity_reasoning && (
          <p className="text-xs text-gray-500 mt-1 italic">🤖 {draft.severity_reasoning}</p>
        )}
      </div>

      {aiMode && draft.hazards.length > 0 && (
        <div>
          <p className="text-sm font-medium text-gray-700 mb-2">Hazards identified by AI</p>
          <div className="flex flex-wrap gap-2">
            {draft.hazards.map((h) => (
              <span
                key={h}
                className="text-xs bg-red-50 text-red-700 border border-red-200 px-2.5 py-1 rounded-full"
              >
                ⚠️ {h}
              </span>
            ))}
          </div>
        </div>
      )}

      {error && (
        <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
          {error}
        </p>
      )}

      <div className="flex gap-3">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 border border-gray-300 text-gray-700 py-2.5 rounded-lg hover:bg-gray-50"
        >
          ← Back
        </button>
        <button
          type="submit"
          disabled={busy}
          className="flex-[2] bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? 'Submitting…' : 'Submit Official Complaint'}
        </button>
      </div>
    </form>
  )
}

export default AiDraftForm
