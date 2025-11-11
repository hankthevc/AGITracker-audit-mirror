/**
 * Dashboard data contracts for FiveThirtyEight-style homepage.
 * 
 * These types define the API contract between backend and frontend
 * for KPI cards, timeseries charts, news feeds, and AI analysis.
 */

export type MetricKey =
  | 'events_per_day'
  | 'swebench_score'
  | 'mmlu_score'
  | 'compute_flops'
  | 'safety_incidents_per_month'
  | 'signposts_completed'

export interface TimePoint {
  t: string  // ISO date
  v: number  // Numeric value
}

export interface Timeseries {
  metric: MetricKey
  series: TimePoint[]
  meta?: Record<string, string | number | boolean>
}

export interface KpiCard {
  key: MetricKey
  label: string
  value: number | string
  deltaPct?: number
  trend?: TimePoint[]
}

export interface NewsItem {
  id: string
  title: string
  source: string
  url: string  // Must be sanitized via SafeLink
  published_at: string
  tags: string[]
  summary?: string  // AI-generated or curated
}

export interface HomepageSnapshot {
  generated_at: string
  kpis: KpiCard[]
  featured: Timeseries[]
  news: NewsItem[]
  analysis: {
    headline: string
    bullets: string[]
    paragraphs: string[]
  }
}

