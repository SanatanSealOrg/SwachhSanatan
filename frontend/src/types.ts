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

export interface AnalyzeWard {
  id: string
  name: string
  ward_number: number | null
  officer_available: boolean
}

export interface AnalyzeResponse {
  draft: AiDraft
  image: { url: string; key: string }
  ward: AnalyzeWard | null
}

export interface AssignmentInfo {
  assigned_at: string | null
  completed_at: string | null
  completion_image_url: string | null
  verified: boolean
  verification_ssim_score: number | null
}

export interface QueueItem {
  id: string
  ticket_number: string
  status: string
  description: string | null
  waste_type: string | null
  severity_score: number
  image_urls: string[]
  ai_waste_type: string | null
  ai_confidence: number | null
  created_at: string | null
  lat: number
  lon: number
  priority_score: number
  priority_band: 'critical' | 'high' | 'medium' | 'low'
  reasons: string[]
  age_days: number
  age_bucket: 'fresh' | 'aging' | 'overdue'
  in_hotspot: boolean
  assignment: { assigned_at: string | null; status: string } | null
}

export interface QueueResponse {
  queue: QueueItem[]
  counts: { fresh: number; aging: number; overdue: number; total: number }
  resolved_total: number
  computed_at: string
}

export interface VerificationResult {
  after_image_url: string
  ssim: number | null
  suspicious_similarity: boolean
  ai: { cleaned: boolean; confidence: number; note: string; source: string }
  verified: boolean
}

export interface ResolveResponse {
  complaint: { id: string; ticket_number: string; status: string }
  verification: VerificationResult | null
  resolved_total: number
}

export interface MyComplaint {
  id: string
  ticket_number: string
  status: string
  description: string | null
  waste_type: string | null
  severity_score: number
  image_urls: string[]
  created_at: string | null
  resolved_at: string | null
  ward_name: string | null
  assignment: AssignmentInfo | null
}

export interface TrackTimelineStep {
  step: 'submitted' | 'assigned' | 'in_progress' | 'resolved'
  at: string | null
  reached: boolean
}

export interface TrackResult {
  ticket_number: string
  status: string
  waste_type: string | null
  severity_score: number
  ward: { name: string; ward_number: number | null } | null
  created_at: string | null
  resolved_at: string | null
  photo_url: string | null
  after_photo_url: string | null
  verified: boolean
  timeline: TrackTimelineStep[]
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
  first_reported: string | null
  chronic: boolean
  ward_id: string | null
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
