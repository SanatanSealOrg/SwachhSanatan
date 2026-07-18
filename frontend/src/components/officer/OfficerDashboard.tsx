import React, { useCallback, useEffect, useMemo, useState } from 'react'
import type { Feature, FeatureCollection } from 'geojson'
import { api, errorMessage } from '../../api'
import { useAuth } from '../../store'
import type { Hotspot, QueueItem, QueueResponse, ResolveResponse } from '../../types'
import AgingTiles, { AgeBucket } from './AgingTiles'
import PriorityQueue from './PriorityQueue'
import OfficerMap from './OfficerMap'
import ResolveModal from './ResolveModal'
import CelebrationOverlay from '../CelebrationOverlay'

interface Celebration {
  result: ResolveResponse
  beforeUrl: string | null
  afterUrl: string | null
}

function OfficerDashboard() {
  const { wardId } = useAuth()
  const [queue, setQueue] = useState<QueueResponse | null>(null)
  const [hotspots, setHotspots] = useState<Hotspot[]>([])
  const [wardFeature, setWardFeature] = useState<Feature | null>(null)
  const [bucket, setBucket] = useState<AgeBucket | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [resolving, setResolving] = useState<QueueItem | null>(null)
  const [celebration, setCelebration] = useState<Celebration | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!wardId) return
    try {
      const [q, h, g] = await Promise.all([
        api.get<QueueResponse>(`/complaints/queue?ward_id=${wardId}`),
        api.get<{ hotspots: Hotspot[] }>(`/hotspots?ward_id=${wardId}`),
        api.get<FeatureCollection>('/wards/geojson?include_dev=true'),
      ])
      setQueue(q.data)
      setHotspots(h.data.hotspots)
      setWardFeature(
        g.data.features.find((f) => f.properties?.id === wardId) ?? null,
      )
      setError('')
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setLoading(false)
    }
  }, [wardId])

  useEffect(() => {
    load()
  }, [load])

  const wardName = (wardFeature?.properties as { name?: string } | undefined)?.name ?? ''

  const filtered = useMemo(() => {
    if (!queue) return []
    return bucket ? queue.queue.filter((c) => c.age_bucket === bucket) : queue.queue
  }, [queue, bucket])

  const chronicCount = hotspots.filter((h) => h.chronic).length

  const start = async (item: QueueItem) => {
    setBusyId(item.id)
    try {
      await api.patch(`/complaints/${item.id}`, { status: 'in_progress' })
      await load()
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setBusyId(null)
    }
  }

  if (!wardId) {
    return <p className="text-gray-500">No ward assigned to this officer account.</p>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between flex-wrap gap-2">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">
            🛡️ Officer Command Center{wardName && ` — ${wardName}`}
          </h2>
          <p className="text-sm text-gray-500">
            AI-prioritized queue, chronic zones and cleanup verification for your ward.
          </p>
        </div>
        {queue && (
          <p className="text-sm text-gray-500">
            🏅 <span className="font-bold text-gray-800">{queue.resolved_total}</span>{' '}
            issues resolved
          </p>
        )}
      </div>

      {error && (
        <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
          {error}
        </p>
      )}

      {loading || !queue ? (
        <p className="text-gray-500">Loading your ward…</p>
      ) : (
        <>
          <AgingTiles counts={queue.counts} selected={bucket} onSelect={setBucket} />

          {chronicCount > 0 && (
            <p className="text-sm bg-purple-50 border border-purple-300 text-purple-800 rounded-lg px-4 py-2">
              ☣️ <strong>{chronicCount}</strong> chronic repeat-offender zone
              {chronicCount > 1 ? 's' : ''} in your ward — shown in purple on the map.
            </p>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="h-[440px] rounded-xl overflow-hidden shadow-lg bg-white">
              <OfficerMap wardFeature={wardFeature} items={queue.queue} hotspots={hotspots} />
            </div>
            <div className="max-h-[440px] overflow-y-auto pr-1">
              <PriorityQueue
                items={filtered}
                busyId={busyId}
                onStart={start}
                onResolve={setResolving}
              />
            </div>
          </div>
        </>
      )}

      {resolving && (
        <ResolveModal
          item={resolving}
          onClose={() => setResolving(null)}
          onResolved={(result, beforeUrl, afterUrl) => {
            setResolving(null)
            setCelebration({ result, beforeUrl, afterUrl })
            load()
          }}
        />
      )}

      {celebration && (
        <CelebrationOverlay
          role="officer"
          wardName={wardName}
          resolvedTotal={celebration.result.resolved_total}
          verification={celebration.result.verification}
          beforeUrl={celebration.beforeUrl}
          afterUrl={
            celebration.result.verification?.after_image_url ?? celebration.afterUrl
          }
          onClose={() => setCelebration(null)}
        />
      )}
    </div>
  )
}

export default OfficerDashboard
