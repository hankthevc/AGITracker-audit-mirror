/**
 * Type definitions for Forecast Aggregator.
 */

export interface Forecast {
  id: number
  source: string
  signpost_code: string
  timeline: string  // ISO date
  confidence: number | null
  quote: string | null
  url: string | null
}

export interface ConsensusData {
  signpost_code: string
  signpost_name: string
  forecast_count: number
  median_timeline: string | null
  mean_timeline: string | null
  earliest_timeline: string | null
  latest_timeline: string | null
  timeline_spread_days: number | null
  mean_confidence: number | null
  forecasts: Forecast[]
}

export interface DistributionData {
  signpost_code: string
  distribution: Array<{
    year: number
    count: number
    median_month: number
  }>
  points: Array<{
    timeline: string
    source: string
    confidence: number | null
    year: number
    month: number
  }>
  stats: {
    count: number
    earliest: string
    latest: string
    median: string
    spread_days: number
  } | null
}

