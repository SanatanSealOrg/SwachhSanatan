import React, { useEffect, useMemo, useState } from 'react'
import { api, errorMessage } from '../api'
import type { Hotspot, MapComplaint, WardMetric } from '../types'
import CityMap from '../components/dashboard/CityMap'
import WardRanking from '../components/dashboard/WardRanking'
import HotspotList from '../components/dashboard/HotspotList'

function StatTile({ label, value, accent }: { label: string; value: string; accent: string }) {
  return (
    <div className="bg-white rounded-xl shadow p-5">
      <p className={`text-3xl font-bold ${accent}`}>{value}</p>
      <p className="text-sm text-gray-500 mt-1">{label}</p>
    </div>
  )
}

function Metrics() {
  const [metrics, setMetrics] = useState<WardMetric[]>([])
  const [wardsGeojson, setWardsGeojson] = useState<GeoJSON.FeatureCollection | null>(null)
  const [hotspots, setHotspots] = useState<Hotspot[]>([])
  const [complaints, setComplaints] = useState<MapComplaint[]>([])
  const [dataKey, setDataKey] = useState(0)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get('/metrics/wards'),
      api.get('/wards/geojson'),
      api.get('/hotspots'),
      api.get('/complaints/map'),
    ])
      .then(([m, g, h, c]) => {
        setMetrics(m.data.metrics)
        setWardsGeojson(g.data)
        setHotspots(h.data.hotspots)
        setComplaints(c.data.complaints)
        setDataKey(Date.now())
      })
      .catch((err) => setError(errorMessage(err)))
      .finally(() => setLoading(false))
  }, [])

  const metricsByWardId = useMemo(
    () => Object.fromEntries(metrics.map((m) => [m.ward_id, m])),
    [metrics],
  )

  const activeWards = metrics.filter((m) => m.total > 0)
  const cityAvgScore = activeWards.length
    ? Math.round(
        activeWards.reduce((sum, m) => sum + m.cleanliness_score, 0) / activeWards.length,
      )
    : 100
  const totalComplaints = metrics.reduce((sum, m) => sum + m.total, 0)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-800 mb-1">🗺️ Live City Dashboard</h2>
        <p className="text-gray-600">
          Real-time waste intelligence for Chennai — cleanliness scores, complaint activity and
          AI-detected hotspots. No sign-in required.
        </p>
      </div>

      {error && (
        <p role="alert" className="text-red-600 text-sm bg-red-50 border border-red-200 rounded p-2">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-gray-500">Loading dashboard…</p>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatTile
              label="Complaints (all wards)"
              value={String(totalComplaints)}
              accent="text-gray-800"
            />
            <StatTile
              label="Open right now"
              value={String(metrics.reduce((s, m) => s + m.open, 0))}
              accent="text-red-600"
            />
            <StatTile
              label="Active hotspots"
              value={String(hotspots.length)}
              accent="text-orange-600"
            />
            <StatTile
              label="City cleanliness score"
              value={`${cityAvgScore}/100`}
              accent={
                cityAvgScore >= 70
                  ? 'text-emerald-600'
                  : cityAvgScore >= 40
                    ? 'text-amber-600'
                    : 'text-red-600'
              }
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 h-[560px] rounded-xl overflow-hidden shadow-lg bg-white">
              <CityMap
                wardsGeojson={wardsGeojson}
                metricsByWardId={metricsByWardId}
                complaints={complaints}
                hotspots={hotspots}
                dataKey={dataKey}
              />
            </div>
            <div className="space-y-6 max-h-[560px] overflow-y-auto pr-1">
              <WardRanking metrics={metrics.filter((m) => !m.ward_name.endsWith('(Dev)'))} />
              <HotspotList hotspots={hotspots} />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 bg-white rounded-lg shadow px-4 py-3">
            <span className="font-semibold text-gray-600">Legend:</span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-red-500 inline-block" /> Open
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" /> In progress
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-green-500 inline-block" /> Resolved
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 rounded-full bg-red-600/40 border border-red-600 inline-block" />{' '}
              AI hotspot
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-3 bg-emerald-500/30 border border-emerald-500 inline-block" />{' '}
              Ward colored by cleanliness score
            </span>
          </div>
        </>
      )}
    </div>
  )
}

export default Metrics
