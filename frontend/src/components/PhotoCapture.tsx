import React, { useEffect, useRef, useState } from 'react'

interface Props {
  file: File | null
  previewUrl: string | null
  latitude: string
  longitude: string
  onFileChange: (file: File | null) => void
  onLatitudeChange: (v: string) => void
  onLongitudeChange: (v: string) => void
  onAnalyze: () => void
  onSkip: () => void
  error: string
}

function PhotoCapture({
  file,
  previewUrl,
  latitude,
  longitude,
  onFileChange,
  onLatitudeChange,
  onLongitudeChange,
  onAnalyze,
  onSkip,
  error,
}: Props) {
  const [locating, setLocating] = useState(false)
  const [locError, setLocError] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      setLocError('Geolocation is not supported by this browser')
      return
    }
    setLocating(true)
    setLocError('')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        onLatitudeChange(pos.coords.latitude.toFixed(6))
        onLongitudeChange(pos.coords.longitude.toFixed(6))
        setLocating(false)
      },
      (err) => {
        setLocError(`Could not get location: ${err.message}. Enter coordinates manually.`)
        setLocating(false)
      },
    )
  }

  useEffect(() => {
    // auto-request location once when the step mounts
    if (navigator.geolocation) useMyLocation()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="space-y-5">
      <div>
        <p className="text-sm text-gray-600 mb-3">
          Snap a photo of the waste issue — our AI will draft the official complaint for you.
        </p>
        {previewUrl ? (
          <div className="relative rounded-xl overflow-hidden shadow-md">
            <img src={previewUrl} alt="Selected waste" className="w-full max-h-80 object-cover" />
            <button
              type="button"
              onClick={() => {
                onFileChange(null)
                if (inputRef.current) inputRef.current.value = ''
              }}
              className="absolute top-2 right-2 bg-black/60 text-white text-xs px-3 py-1.5 rounded-full hover:bg-black/80"
            >
              ✕ Change photo
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="w-full border-2 border-dashed border-gray-300 rounded-xl py-12 flex flex-col items-center gap-2 text-gray-500 hover:border-green-500 hover:text-green-600 transition-colors"
          >
            <span className="text-4xl">📷</span>
            <span className="font-medium">Tap to take or choose a photo</span>
            <span className="text-xs">jpg / png / webp, max 5MB</span>
          </button>
        )}
        <input
          ref={inputRef}
          id="photo"
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          capture="environment"
          className="hidden"
          onChange={(e) => onFileChange(e.target.files?.[0] ?? null)}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="latitude" className="block text-sm font-medium text-gray-700 mb-1">
            Latitude
          </label>
          <input
            id="latitude"
            required
            value={latitude}
            onChange={(e) => onLatitudeChange(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
        </div>
        <div>
          <label htmlFor="longitude" className="block text-sm font-medium text-gray-700 mb-1">
            Longitude
          </label>
          <input
            id="longitude"
            required
            value={longitude}
            onChange={(e) => onLongitudeChange(e.target.value)}
            className="w-full border border-gray-300 rounded px-3 py-2"
          />
        </div>
      </div>
      <button
        type="button"
        onClick={useMyLocation}
        disabled={locating}
        className="text-sm text-blue-700 hover:underline disabled:opacity-50"
      >
        {locating ? 'Locating…' : '📍 Use my current location'}
      </button>
      {locError && <p className="text-amber-700 text-sm">{locError}</p>}

      {error && (
        <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
          {error}
        </p>
      )}

      <button
        type="button"
        onClick={onAnalyze}
        disabled={!file}
        className="w-full bg-gradient-to-r from-green-600 to-emerald-500 text-white py-3 rounded-lg font-semibold shadow hover:from-green-700 hover:to-emerald-600 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
      >
        ✨ Analyze with AI
      </button>
      <button
        type="button"
        onClick={onSkip}
        className="w-full text-sm text-gray-500 hover:text-gray-700 hover:underline"
      >
        Skip — fill the form manually
      </button>
    </div>
  )
}

export default PhotoCapture
