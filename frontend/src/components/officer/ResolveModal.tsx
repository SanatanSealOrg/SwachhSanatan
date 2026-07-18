import React, { useEffect, useRef, useState } from 'react'
import { api, errorMessage } from '../../api'
import type { QueueItem, ResolveResponse } from '../../types'
import CameraCapture from '../CameraCapture'

interface Props {
  item: QueueItem
  onResolved: (result: ResolveResponse, beforeUrl: string | null, afterLocalUrl: string | null) => void
  onClose: () => void
}

function ResolveModal({ item, onResolved, onClose }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [notes, setNotes] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [cameraOpen, setCameraOpen] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const objectUrlRef = useRef<string | null>(null)
  const cameraSupported = Boolean(navigator.mediaDevices?.getUserMedia)

  const setAfterFile = (f: File | null) => {
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

  const submit = async (withPhoto: boolean) => {
    setError('')
    setBusy(true)
    try {
      const form = new FormData()
      if (withPhoto && file) form.append('file', file)
      if (notes) form.append('notes', notes)
      const { data } = await api.post<ResolveResponse>(
        `/complaints/${item.id}/resolve`,
        form,
      )
      onResolved(data, item.image_urls[0] ?? null, withPhoto ? previewUrl : null)
    } catch (err) {
      setError(errorMessage(err))
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[1100] bg-black/60 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-gray-800">
            Resolve {item.ticket_number}
          </h3>
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="text-gray-400 hover:text-gray-700"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
              Before (reported)
            </p>
            {item.image_urls[0] ? (
              <img
                src={item.image_urls[0]}
                alt="Before"
                className="rounded-lg h-32 w-full object-cover"
              />
            ) : (
              <div className="rounded-lg h-32 bg-gray-100 flex items-center justify-center text-gray-400 text-xs">
                No photo
              </div>
            )}
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wide text-gray-400 mb-1">
              After (your photo)
            </p>
            {previewUrl ? (
              <div className="relative">
                <img src={previewUrl} alt="After" className="rounded-lg h-32 w-full object-cover" />
                <button
                  type="button"
                  onClick={() => setAfterFile(null)}
                  className="absolute top-1 right-1 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded-full"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="rounded-lg h-32 border-2 border-dashed border-gray-300 flex flex-col items-center justify-center gap-1">
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => inputRef.current?.click()}
                    className="text-xs bg-gray-100 hover:bg-gray-200 rounded px-2 py-1"
                  >
                    🖼️ Upload
                  </button>
                  {cameraSupported && (
                    <button
                      type="button"
                      onClick={() => setCameraOpen(true)}
                      className="text-xs bg-gray-100 hover:bg-gray-200 rounded px-2 py-1"
                    >
                      📸 Camera
                    </button>
                  )}
                </div>
                <p className="text-[10px] text-gray-400">proof of cleanup</p>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept="image/jpeg,image/png,image/gif,image/webp"
              capture="environment"
              className="hidden"
              onChange={(e) => setAfterFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        <textarea
          rows={2}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Notes (optional)"
          className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
        />

        {error && (
          <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
            {error}
          </p>
        )}

        <button
          type="button"
          disabled={busy || !file}
          onClick={() => submit(true)}
          className="w-full bg-green-600 text-white py-2.5 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-40"
        >
          {busy ? '🤖 Verifying with AI…' : 'Upload & Verify ✓'}
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => submit(false)}
          className="w-full text-sm text-gray-500 hover:text-gray-700 hover:underline disabled:opacity-50"
        >
          Resolve without photo
        </button>

        {cameraOpen && (
          <CameraCapture
            onCapture={(f) => {
              setAfterFile(f)
              setCameraOpen(false)
            }}
            onClose={() => setCameraOpen(false)}
          />
        )}
      </div>
    </div>
  )
}

export default ResolveModal
