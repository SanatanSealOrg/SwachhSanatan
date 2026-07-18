export interface AiDraft {
  waste_type: string | null
  severity: number
  severity_reasoning: string
  confidence: number
  title: string
  description: string
  hazards: string[]
  is_waste_visible: boolean
  source: 'openai' | 'mock'
}

export interface AnalyzeResponse {
  draft: AiDraft
  image: { url: string; key: string }
}

export interface WardMetric {
  ward_id: string
  ward_name: string
  ward_number: number | null
  total: number
  open: number
  in_progress: number
  resolved: number
  resolution_rate: number | null
  cleanliness_score: number
  band: 'green' | 'yellow' | 'red'
  avg_resolution_hours: number | null
}

export interface Hotspot {
  id: number
  centroid: { lat: number; lon: number }
  radius_m: number
  count: number
  dominant_waste_type: string | null
  avg_severity: number
  last_reported: string | null
}

export interface MapComplaint {
  id: string
  ticket_number: string
  status: string
  waste_type: string | null
  severity_score: number
  created_at: string | null
  lat: number
  lon: number
  thumbnail_url: string | null
}
