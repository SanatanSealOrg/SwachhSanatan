import React, { useMemo } from 'react'
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Circle, Popup, Tooltip } from 'react-leaflet'
import L from 'leaflet'
import type { Feature } from 'geojson'
import 'leaflet/dist/leaflet.css'
import type { Hotspot, QueueItem } from '../../types'

const BAND_COLORS: Record<string, string> = {
  critical: '#dc2626',
  high: '#f97316',
  medium: '#eab308',
  low: '#9ca3af',
}

interface Props {
  wardFeature: Feature | null
  items: QueueItem[]
  hotspots: Hotspot[]
}

function OfficerMap({ wardFeature, items, hotspots }: Props) {
  const bounds = useMemo(() => {
    // Prefer fitting to where the action is (complaints + hotspots) — the
    // city-wide desk ward's polygon spans all of Chennai and would zoom
    // way out. Fall back to the ward polygon when the queue is empty.
    const allPoints: [number, number][] = [
      ...items.map((c) => [c.lat, c.lon] as [number, number]),
      ...hotspots.map((h) => [h.centroid.lat, h.centroid.lon] as [number, number]),
    ]
    // Fit to the main cluster only: far-away outliers (e.g. an out-of-city
    // complaint routed to the city-wide desk) stay visible as markers but
    // must not zoom the map out to half the country.
    const median = (vals: number[]) => {
      const s = [...vals].sort((a, b) => a - b)
      return s[Math.floor(s.length / 2)]
    }
    let points = allPoints
    if (allPoints.length > 2) {
      const mLat = median(allPoints.map((p) => p[0]))
      const mLon = median(allPoints.map((p) => p[1]))
      const near = allPoints.filter(
        ([lat, lon]) => Math.abs(lat - mLat) < 0.5 && Math.abs(lon - mLon) < 0.5,
      )
      if (near.length > 0) points = near
    }
    if (points.length === 1) {
      // zero-area bounds would zoom to max — give a single point some room
      const [lat, lon] = points[0]
      return L.latLngBounds([lat - 0.01, lon - 0.01], [lat + 0.01, lon + 0.01])
    }
    if (points.length > 1) {
      return L.latLngBounds(points).pad(0.25)
    }
    if (!wardFeature) return null
    try {
      return L.geoJSON(wardFeature as GeoJSON.GeoJsonObject).getBounds()
    } catch {
      return null
    }
  }, [wardFeature, items, hotspots])

  if (!bounds) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400 text-sm">
        Ward boundary unavailable
      </div>
    )
  }

  return (
    <MapContainer bounds={bounds} scrollWheelZoom className="h-full w-full">
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {wardFeature && (
        <GeoJSON
          data={wardFeature}
          style={{ color: '#16a34a', weight: 2, fillColor: '#16a34a', fillOpacity: 0.06 }}
        />
      )}

      {hotspots.map((h) => (
        <Circle
          key={`hs-${h.id}`}
          center={[h.centroid.lat, h.centroid.lon]}
          radius={h.radius_m}
          pathOptions={
            h.chronic
              ? { color: '#7c3aed', weight: 3, dashArray: '6 6', fillColor: '#7c3aed', fillOpacity: 0.35 }
              : { color: '#dc2626', weight: 2, fillColor: '#dc2626', fillOpacity: 0.3 }
          }
        >
          <Tooltip direction="top" sticky>
            {h.chronic ? (
              <span>
                ☣️ REPEAT OFFENDER ZONE — active since{' '}
                {h.first_reported ? new Date(h.first_reported).toLocaleDateString() : 'a while'},{' '}
                {h.count} reports
              </span>
            ) : (
              <span>
                🔥 Hotspot — {h.count} reports · avg severity {h.avg_severity}
              </span>
            )}
          </Tooltip>
        </Circle>
      ))}

      {items.map((c) => (
        <CircleMarker
          key={c.id}
          center={[c.lat, c.lon]}
          radius={6}
          pathOptions={{
            color: '#ffffff',
            weight: 1,
            fillColor: BAND_COLORS[c.priority_band],
            fillOpacity: 0.95,
          }}
        >
          <Popup>
            <div className="text-sm space-y-1 min-w-[150px]">
              <p className="font-mono font-bold">{c.ticket_number}</p>
              <p className="capitalize">
                {c.priority_band} priority · score {c.priority_score}
              </p>
              <p>
                Severity {c.severity_score} · {Math.round(c.age_days)}d old
              </p>
              {c.image_urls[0] && (
                <img
                  src={c.image_urls[0]}
                  alt="Complaint"
                  className="mt-1 rounded max-h-24 w-full object-cover"
                />
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}

export default OfficerMap
