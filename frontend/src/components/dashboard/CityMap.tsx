import React from 'react'
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Circle, Popup, Tooltip } from 'react-leaflet'
import type { Layer } from 'leaflet'
import type { Feature } from 'geojson'
import 'leaflet/dist/leaflet.css'
import type { Hotspot, MapComplaint, WardMetric } from '../../types'

const BAND_COLORS: Record<string, string> = {
  green: '#22c55e',
  yellow: '#eab308',
  red: '#ef4444',
}

const STATUS_COLORS: Record<string, string> = {
  open: '#ef4444',
  assigned: '#f59e0b',
  in_progress: '#f59e0b',
  resolved: '#22c55e',
  rejected: '#9ca3af',
}

const WASTE_LABELS: Record<string, string> = {
  bin: 'Overflowing Bin',
  dumping: 'Illegal Dumping',
  construction: 'Construction Debris',
  biohazard: 'Biohazard',
}

interface Props {
  wardsGeojson: GeoJSON.FeatureCollection | null
  metricsByWardId: Record<string, WardMetric>
  complaints: MapComplaint[]
  hotspots: Hotspot[]
  dataKey: number
}

function CityMap({ wardsGeojson, metricsByWardId, complaints, hotspots, dataKey }: Props) {
  const styleWard = (feature?: Feature) => {
    const id = feature?.properties?.id as string | undefined
    const band = (id && metricsByWardId[id]?.band) || 'green'
    return {
      color: BAND_COLORS[band],
      weight: 2,
      fillColor: BAND_COLORS[band],
      fillOpacity: 0.22,
    }
  }

  const onEachWard = (feature: Feature, layer: Layer) => {
    const props = feature.properties as { id: string; name: string }
    const metric = metricsByWardId[props.id]
    const score = metric ? `${metric.cleanliness_score}/100` : 'n/a'
    layer.bindTooltip(`<strong>${props.name}</strong><br/>Cleanliness: ${score}`, {
      sticky: true,
    })
  }

  return (
    <MapContainer
      center={[13.04, 80.24]}
      zoom={12}
      scrollWheelZoom
      className="h-full w-full"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />

      {wardsGeojson && (
        <GeoJSON
          key={dataKey}
          data={wardsGeojson}
          style={styleWard}
          onEachFeature={onEachWard}
        />
      )}

      {hotspots.map((h) => (
        <Circle
          key={`hotspot-${h.id}`}
          center={[h.centroid.lat, h.centroid.lon]}
          radius={h.radius_m}
          pathOptions={{ color: '#dc2626', weight: 2, fillColor: '#dc2626', fillOpacity: 0.3 }}
        >
          <Tooltip direction="top" sticky>
            🔥 Hotspot — {h.count} reports · {WASTE_LABELS[h.dominant_waste_type ?? ''] ?? 'Mixed waste'} ·
            avg severity {h.avg_severity}
          </Tooltip>
        </Circle>
      ))}

      {complaints.map((c) => (
        <CircleMarker
          key={c.id}
          center={[c.lat, c.lon]}
          radius={5}
          pathOptions={{
            color: '#ffffff',
            weight: 1,
            fillColor: STATUS_COLORS[c.status] ?? '#6b7280',
            fillOpacity: 0.9,
          }}
        >
          <Popup>
            <div className="text-sm space-y-1 min-w-[160px]">
              <p className="font-mono font-bold">{c.ticket_number}</p>
              <p>
                {WASTE_LABELS[c.waste_type ?? ''] ?? 'Waste issue'} · severity {c.severity_score}
              </p>
              <p className="capitalize">Status: {c.status.replace('_', ' ')}</p>
              {c.created_at && (
                <p className="text-gray-500">{new Date(c.created_at).toLocaleDateString()}</p>
              )}
              {c.thumbnail_url && (
                <img
                  src={c.thumbnail_url}
                  alt="Complaint"
                  className="mt-1 rounded max-h-28 w-full object-cover"
                />
              )}
            </div>
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  )
}

export default CityMap
