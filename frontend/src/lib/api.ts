/**
 * ClaimIQ — API Client
 * All calls to the FastAPI backend go through here.
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  timeout: 60000, // 60s — OCR + AI can take time
})

export interface ScoreBreakdown {
  completeness: number
  consistency: number
  fraud_signals: number
  documentation: number
}

export interface Flag {
  field: string
  message: string
  message_de: string
  severity: 'error' | 'warning' | 'info'
}

export interface ChecklistItem {
  item: string
  item_de: string
  required: boolean
}

export interface ClaimResult {
  claim_id: string
  status: 'pending' | 'processing' | 'done' | 'error'
  created_at: string
  claim_vertical: string
  summary: string | null
  summary_de: string | null
  structured_data: Record<string, unknown> | null
  readiness_score: number | null
  score_breakdown: ScoreBreakdown | null
  flags: Flag[] | null
  action_checklist: ChecklistItem[] | null
  suggestion: 'approve' | 'review' | 'reject' | null
  ocr_engine: string | null
  error_message: string | null
}

export interface UploadResponse {
  claim_id: string
  status: string
  message: string
}

export interface FeedbackPayload {
  field_corrected?: string
  original_value?: string
  corrected_value?: string
  general_comment?: string
}

// Upload document and get full analysis
export async function uploadClaim(
  file: File,
  sessionId?: string
): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const params = sessionId ? `?session_id=${sessionId}` : ''
  const { data } = await api.post<UploadResponse>(`/claims/upload${params}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

// Get claim result by ID
export async function getClaimResult(claimId: string): Promise<ClaimResult> {
  const { data } = await api.get<ClaimResult>(`/claims/${claimId}`)
  return data
}

// Submit feedback / correction
export async function submitFeedback(
  claimId: string,
  feedback: FeedbackPayload
): Promise<void> {
  await api.post(`/claims/${claimId}/feedback`, feedback)
}

// Get PDF download URL
export function getPdfUrl(claimId: string): string {
  return `${API_URL}/api/v1/claims/${claimId}/pdf`
}

export default api
