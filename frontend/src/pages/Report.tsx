import React, { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorMessage } from '../api'
import type { AiDraft, AnalyzeResponse, AnalyzeWard } from '../types'
import PhotoCapture from '../components/PhotoCapture'
import AiAnalysisProgress from '../components/AiAnalysisProgress'
import AiDraftForm, { DraftFields } from '../components/AiDraftForm'

// Chennai city centre — fallback when geolocation is unavailable
const DEFAULT_LAT = 13.0827
const DEFAULT_LON = 80.2707

type Step = 'capture' | 'analyzing' | 'review' | 'done'

function Report() {
  const [step, setStep] = useState<Step>('capture')
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [latitude, setLatitude] = useState(String(DEFAULT_LAT))
  const [longitude, setLongitude] = useState(String(DEFAULT_LON))
  const [draft, setDraft] = useState<AiDraft | null>(null)
  const [ward, setWard] = useState<AnalyzeWard | null>(null)
  const [imageRef, setImageRef] = useState<{ url: string; key: string } | null>(null)
  const [analysisDone, setAnalysisDone] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [ticket, setTicket] = useState<string | null>(null)
  const objectUrlRef = useRef<string | null>(null)

  const handleFileChange = (f: File | null) => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
    objectUrlRef.current = f ? URL.createObjectURL(f) : null
    setFile(f)
    setPreviewUrl(objectUrlRef.current)
  }

  useEffect(
    () => () => {
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current)
    },
    [],
  )

  const analyze = async () => {
    if (!file) {
      setError('A photo is required')
      return
    }
    setError('')
    setAnalysisDone(false)
    setStep('analyzing')
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('latitude', latitude)
      form.append('longitude', longitude)
      const { data } = await api.post<AnalyzeResponse>('/complaints/analyze', form)
      setDraft(data.draft)
      setImageRef(data.image)
      setWard(data.ward)
      setAnalysisDone(true)
    } catch (err) {
      setError(errorMessage(err))
      setStep('capture')
    }
  }

  const skipToManual = () => {
    if (!file) {
      setError('A photo is required')
      return
    }
    setError('')
    setDraft(null)
    setWard(null)
    setImageRef(null)
    setStep('review')
  }

  const submit = async (fields: DraftFields) => {
    setError('')
    setBusy(true)
    try {
      const form = new FormData()
      const description = fields.title
        ? `${fields.title} — ${fields.description}`
        : fields.description
      form.append('description', description)
      form.append('latitude', latitude)
      form.append('longitude', longitude)
      form.append('waste_type', fields.wasteType)
      form.append('severity_score', String(fields.severity))
      if (draft && imageRef) {
        // reuse the image staged during AI analysis — no re-upload
        form.append('image_key', imageRef.key)
        if (draft.waste_type) form.append('ai_waste_type', draft.waste_type)
        form.append('ai_confidence', String(draft.confidence))
      } else if (file) {
        form.append('file', file)
      }
      const { data } = await api.post('/complaints', form)
      setTicket(data.ticket_number)
      setStep('done')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const reset = () => {
    handleFileChange(null)
    setDraft(null)
    setWard(null)
    setImageRef(null)
    setTicket(null)
    setError('')
    setStep('capture')
  }

  if (step === 'done' && ticket) {
    return (
      <div className="max-w-lg mx-auto bg-white rounded-lg shadow-lg p-8 text-center">
        <p className="text-5xl mb-4">✅</p>
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Complaint Submitted</h2>
        <p className="text-gray-600 mb-4">Your ticket number is</p>
        <p data-testid="ticket-number" className="text-2xl font-mono font-bold text-green-700 mb-6">
          {ticket}
        </p>
        {ward && (
          <p className="text-sm text-blue-700 mb-3">📍 Reported in {ward.name}</p>
        )}
        <p className="mb-4">
          <Link to={`/track/${ticket}`} className="text-blue-700 hover:underline text-sm">
            🔎 Track this complaint
          </Link>
        </p>
        {draft && (
          <p className="text-sm text-gray-500 mb-6">
            🤖 This complaint was drafted by AI and reviewed by you — it is now in the
            municipal queue for assignment.
          </p>
        )}
        <button
          onClick={reset}
          className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
        >
          Report Another Issue
        </button>
      </div>
    )
  }

  return (
    <div className="max-w-lg mx-auto bg-white rounded-lg shadow-lg p-8">
      <h2 className="text-2xl font-bold text-gray-800 mb-1">📱 Report a Waste Issue</h2>
      <p className="text-sm text-gray-500 mb-6">
        {step === 'capture' && 'Step 1 of 3 — photo & location'}
        {step === 'analyzing' && 'Step 2 of 3 — AI analysis'}
        {step === 'review' && 'Step 3 of 3 — review & submit'}
      </p>

      {step === 'capture' && (
        <PhotoCapture
          file={file}
          previewUrl={previewUrl}
          latitude={latitude}
          longitude={longitude}
          onFileChange={handleFileChange}
          onLatitudeChange={setLatitude}
          onLongitudeChange={setLongitude}
          onAnalyze={analyze}
          onSkip={skipToManual}
          error={error}
        />
      )}

      {step === 'analyzing' && (
        <AiAnalysisProgress
          previewUrl={previewUrl}
          done={analysisDone}
          onFinished={() => setStep('review')}
        />
      )}

      {step === 'review' && (
        <AiDraftForm
          key={draft ? 'ai' : 'manual'}
          previewUrl={previewUrl}
          draft={draft}
          ward={draft ? ward : null}
          busy={busy}
          error={error}
          onSubmit={submit}
          onBack={() => {
            setError('')
            setStep('capture')
          }}
        />
      )}
    </div>
  )
}

export default Report
