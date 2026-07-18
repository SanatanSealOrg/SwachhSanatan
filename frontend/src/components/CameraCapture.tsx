import React, { useEffect, useRef, useState } from 'react'

interface Props {
  onCapture: (file: File) => void
  onClose: () => void
}

function CameraCapture({ onCapture, onClose }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const [error, setError] = useState('')
  const [ready, setReady] = useState(false)

  useEffect(() => {
    let cancelled = false
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: 'environment' }, audio: false })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop())
          return
        }
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
        setReady(true)
      })
      .catch((err: DOMException) => {
        setError(
          err.name === 'NotAllowedError'
            ? 'Camera permission denied — you can still upload a photo instead.'
            : `Could not open camera (${err.message}) — use photo upload instead.`,
        )
      })
    return () => {
      cancelled = true
      streamRef.current?.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
  }, [])

  const stopStream = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
  }

  const capture = () => {
    const video = videoRef.current
    if (!video || !video.videoWidth) return
    const canvas = document.createElement('canvas')
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    canvas.getContext('2d')?.drawImage(video, 0, 0)
    canvas.toBlob(
      (blob) => {
        if (blob) {
          onCapture(
            new File([blob], `camera_${Date.now()}.jpg`, { type: 'image/jpeg' }),
          )
        }
        stopStream()
      },
      'image/jpeg',
      0.9,
    )
  }

  return (
    <div className="fixed inset-0 z-[1200] bg-black/80 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <h3 className="font-bold text-gray-800">📸 Take a photo</h3>
          <button
            type="button"
            onClick={() => {
              stopStream()
              onClose()
            }}
            className="text-gray-500 hover:text-gray-800 text-lg"
            aria-label="Close camera"
          >
            ✕
          </button>
        </div>

        {error ? (
          <div className="p-6 text-center space-y-4">
            <p className="text-amber-700 text-sm bg-amber-50 border border-amber-200 rounded p-3">
              {error}
            </p>
            <button
              type="button"
              onClick={onClose}
              className="bg-gray-700 text-white px-5 py-2 rounded hover:bg-gray-800"
            >
              Close
            </button>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full max-h-[60vh] bg-black object-contain"
            />
            <div className="p-4 flex justify-center">
              <button
                type="button"
                onClick={capture}
                disabled={!ready}
                className="w-16 h-16 rounded-full bg-green-600 hover:bg-green-700 disabled:opacity-40 border-4 border-white shadow-lg ring-2 ring-green-600 text-2xl"
                aria-label="Capture photo"
              >
                📷
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default CameraCapture
