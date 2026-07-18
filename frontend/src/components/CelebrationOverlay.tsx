import React, { useEffect, useMemo } from 'react'
import Confetti from './Confetti'
import type { VerificationResult } from '../types'

const OFFICER_MESSAGES = [
  'You just made {ward} safer — cleaner streets, healthier children 👏',
  "That's one less health hazard on Chennai's streets 🙌",
  'The neighbourhood breathes easier because of you 🌿',
  'Families in {ward} thank you — their streets are cleaner today 💚',
]

const CITIZEN_MESSAGES = [
  'Your report made this happen — {ward} is cleaner because you spoke up 👏',
  'Look at the change you created — one photo, one cleaner street 🌿',
  'This is your impact: a healthier {ward} for everyone 💚',
]

interface Props {
  role: 'officer' | 'citizen'
  wardName: string
  resolvedTotal?: number
  verification?: VerificationResult | null
  beforeUrl?: string | null
  afterUrl?: string | null
  onClose: () => void
}

function CelebrationOverlay({
  role,
  wardName,
  resolvedTotal,
  verification,
  beforeUrl,
  afterUrl,
  onClose,
}: Props) {
  const message = useMemo(() => {
    const pool = role === 'officer' ? OFFICER_MESSAGES : CITIZEN_MESSAGES
    return pool[Math.floor(Math.random() * pool.length)].replace(
      '{ward}',
      wardName || 'your ward',
    )
  }, [role, wardName])

  useEffect(() => {
    const t = window.setTimeout(onClose, 8000)
    return () => window.clearTimeout(t)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-[1150] bg-black/60 flex items-center justify-center p-4">
      <Confetti />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center space-y-4">
        <button
          type="button"
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-700"
          aria-label="Close celebration"
        >
          ✕
        </button>
        <p className="text-6xl animate-bounce">👏</p>
        <h3 className="text-xl font-bold text-gray-800">
          {role === 'officer' ? 'Outstanding work!' : 'You made a difference!'}
        </h3>
        <p className="text-gray-700">{message}</p>

        {(beforeUrl || afterUrl) && (
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">Before</p>
              {beforeUrl ? (
                <img src={beforeUrl} alt="Before" className="rounded-lg h-28 w-full object-cover" />
              ) : (
                <div className="rounded-lg h-28 bg-gray-100" />
              )}
            </div>
            <div>
              <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">After</p>
              {afterUrl ? (
                <img src={afterUrl} alt="After" className="rounded-lg h-28 w-full object-cover" />
              ) : (
                <div className="rounded-lg h-28 bg-gray-100 flex items-center justify-center text-2xl">
                  ✨
                </div>
              )}
            </div>
          </div>
        )}

        {verification?.verified && (
          <p className="text-sm bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg px-3 py-2">
            🤖 AI verified: waste cleared
            {verification.ssim != null && ` (scene change score ${(1 - verification.ssim).toFixed(2)})`}
          </p>
        )}
        {verification?.suspicious_similarity && (
          <p className="text-xs bg-amber-50 border border-amber-200 text-amber-800 rounded-lg px-3 py-2">
            ⚠️ The after photo looks very similar to the original — flagged for review.
          </p>
        )}

        {role === 'officer' && resolvedTotal != null && (
          <p className="text-sm text-gray-500">
            You've resolved <span className="font-bold text-gray-800">{resolvedTotal}</span>{' '}
            issues in {wardName || 'your ward'} 🏅
          </p>
        )}
      </div>
    </div>
  )
}

export default CelebrationOverlay
