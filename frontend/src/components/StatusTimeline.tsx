import React from 'react'

export interface TimelineStep {
  label: string
  at: string | null
  reached: boolean
}

const STATUS_ORDER: Record<string, number> = {
  open: 0,
  assigned: 1,
  in_progress: 2,
  resolved: 3,
}

/** Build the 4 standard steps from a complaint's status + known timestamps. */
export function buildSteps(
  status: string,
  createdAt: string | null,
  assignedAt: string | null,
  resolvedAt: string | null,
): TimelineStep[] {
  const ordinal = STATUS_ORDER[status] ?? 0
  return [
    { label: 'Submitted', at: createdAt, reached: true },
    { label: 'Assigned', at: ordinal >= 1 ? assignedAt : null, reached: ordinal >= 1 },
    { label: 'In Progress', at: null, reached: ordinal >= 2 },
    { label: 'Resolved', at: resolvedAt, reached: ordinal >= 3 },
  ]
}

function StatusTimeline({ steps, rejected }: { steps: TimelineStep[]; rejected?: boolean }) {
  return (
    <div className="flex items-start">
      {steps.map((s, i) => (
        <React.Fragment key={s.label}>
          {i > 0 && (
            <div
              className={`flex-1 h-0.5 mt-3 ${s.reached ? 'bg-emerald-500' : 'bg-gray-200'}`}
            />
          )}
          <div className="flex flex-col items-center w-16 shrink-0">
            <span
              className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                s.reached
                  ? 'bg-emerald-500 text-white'
                  : 'bg-gray-200 text-gray-400'
              }`}
            >
              {s.reached ? '✓' : i + 1}
            </span>
            <p
              className={`text-[10px] mt-1 text-center ${
                s.reached ? 'text-gray-700 font-medium' : 'text-gray-400'
              }`}
            >
              {s.label}
            </p>
            {s.at && (
              <p className="text-[9px] text-gray-400 text-center">
                {new Date(s.at).toLocaleDateString()}
              </p>
            )}
          </div>
        </React.Fragment>
      ))}
      {rejected && (
        <span className="ml-2 mt-2 text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-semibold">
          Rejected
        </span>
      )}
    </div>
  )
}

export default StatusTimeline
