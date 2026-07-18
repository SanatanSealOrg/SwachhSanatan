import React, { useEffect, useRef, useState } from 'react'

const STEPS = [
  { icon: '📤', label: 'Uploading photo', detail: 'Securely sending your photo…' },
  { icon: '🔍', label: 'Examining image', detail: 'AI vision is scanning the scene…' },
  { icon: '🗑️', label: 'Detecting waste type', detail: 'Identifying the kind of waste…' },
  { icon: '⚠️', label: 'Assessing severity', detail: 'Judging urgency and public-health impact…' },
  { icon: '📝', label: 'Drafting official report', detail: 'Writing your complaint in official language…' },
  { icon: '🗺️', label: 'Mapping ward & assigning officer', detail: 'Locating your ward and its sanitation officer…' },
]

const STEP_MS = 1300

interface Props {
  previewUrl: string | null
  done: boolean
  onFinished: () => void
}

function AiAnalysisProgress({ previewUrl, done, onFinished }: Props) {
  const [activeStep, setActiveStep] = useState(0)
  const [progress, setProgress] = useState(0)
  const finishedRef = useRef(false)

  useEffect(() => {
    const start = Date.now()
    const timer = window.setInterval(() => {
      const elapsed = Date.now() - start
      if (done) {
        // snap to completion: fill the bar, complete all steps, then hand off
        setActiveStep(STEPS.length)
        setProgress((p) => Math.min(100, p + 6))
      } else {
        setActiveStep(Math.min(Math.floor(elapsed / STEP_MS), STEPS.length - 1))
        // ease toward 90% while the real request is in flight
        setProgress((p) => p + (90 - p) * 0.025)
      }
    }, 100)
    return () => window.clearInterval(timer)
  }, [done])

  useEffect(() => {
    if (done && progress >= 100 && !finishedRef.current) {
      finishedRef.current = true
      window.setTimeout(onFinished, 400)
    }
  }, [done, progress, onFinished])

  const current = Math.min(activeStep, STEPS.length - 1)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        {previewUrl && (
          <img
            src={previewUrl}
            alt="Analyzing"
            className="w-20 h-20 rounded-xl object-cover shadow-md animate-pulse"
          />
        )}
        <div>
          <h3 className="text-lg font-bold text-gray-800">AI is analyzing your photo</h3>
          <p className="text-sm text-gray-500">{STEPS[current].detail}</p>
        </div>
      </div>

      <div>
        <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 to-emerald-400 transition-all duration-150 ease-out"
            style={{ width: `${Math.min(progress, 100)}%` }}
          />
        </div>
        <p className="text-right text-xs text-gray-400 mt-1">{Math.round(Math.min(progress, 100))}%</p>
      </div>

      <ul className="space-y-3">
        {STEPS.map((step, i) => {
          const isDone = i < activeStep
          const isActive = i === activeStep && !done
          return (
            <li
              key={step.label}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 transition-all duration-300 ${
                isActive
                  ? 'bg-green-50 border border-green-200 shadow-sm'
                  : isDone
                    ? 'opacity-90'
                    : 'opacity-40'
              }`}
            >
              <span
                className={`w-8 h-8 flex items-center justify-center rounded-full text-sm ${
                  isDone
                    ? 'bg-green-500 text-white'
                    : isActive
                      ? 'bg-white border-2 border-green-500 animate-pulse'
                      : 'bg-gray-100'
                }`}
              >
                {isDone ? '✓' : step.icon}
              </span>
              <span
                className={`text-sm font-medium ${
                  isDone ? 'text-green-700' : isActive ? 'text-gray-800' : 'text-gray-400'
                }`}
              >
                {step.label}
                {isActive && <span className="ml-1 animate-pulse">…</span>}
              </span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default AiAnalysisProgress
