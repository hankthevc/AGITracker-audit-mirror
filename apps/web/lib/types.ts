/**
 * Shared TypeScript types for the web application.
 */

export interface SignpostLink {
  signpost_id: number
  signpost_code: string
  signpost_name: string
  signpost_title?: string  // Alias for signpost_name
  category?: string
  confidence: number | null
  value: number | null
  rationale?: string
}

export interface Event {
  id: number
  title: string
  summary: string | null
  source_url: string
  publisher: string | null
  published_at: string | null
  date?: string  // Alias for published_at
  evidence_tier: 'A' | 'B' | 'C' | 'D'
  tier?: 'A' | 'B' | 'C' | 'D'  // Alias for evidence_tier
  source_type: 'news' | 'paper' | 'blog' | 'leaderboard' | 'gov'
  provisional: boolean
  needs_review: boolean
  signpost_links?: SignpostLink[]
}

export interface ImpactTimeline {
  short: string  // Impact in 0-6 months
  medium: string  // Impact in 6-18 months
  long: string  // Impact beyond 18 months
}

export interface EventAnalysis {
  event_id: number
  summary: string | null
  relevance_explanation: string | null
  impact_json: ImpactTimeline | null
  confidence_reasoning: string | null
  significance_score: number | null  // 0.0-1.0
  llm_version: string | null
  generated_at: string
}

export interface EventWithAnalysis extends Event {
  analysis?: EventAnalysis
}

export interface EventsResponse {
  total: number
  skip: number
  limit: number
  results: Event[]
  items?: Event[]  // Alias for results
}

