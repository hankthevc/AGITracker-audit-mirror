/**
 * API client for AGI Signpost Tracker
 */

import { getApiBaseUrl } from './apiBase'
import { fetchJson } from './fetchJson'

export async function fetcher(url: string) {
  const baseUrl = getApiBaseUrl()
  return fetchJson(`${baseUrl}${url}`)
}

export const apiClient = {
  getIndex: async (preset: string = 'equal', date?: string) => {
    const params = new URLSearchParams({ preset })
    if (date) params.append('date', date)
    return fetcher(`/v1/index?${params}`)
  },
  
  getSignposts: async (category?: string, firstClass?: boolean) => {
    const params = new URLSearchParams()
    if (category) params.append('category', category)
    if (firstClass !== undefined) params.append('first_class', String(firstClass))
    return fetcher(`/v1/signposts?${params}`)
  },
  
  getSignpost: async (id: number) => {
    return fetcher(`/v1/signposts/${id}`)
  },
  
  getEvidence: async (signpostId?: number, tier?: string, skip: number = 0, limit: number = 50) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    if (signpostId) params.append('signpost_id', String(signpostId))
    if (tier) params.append('tier', tier)
    return fetcher(`/v1/evidence?${params}`)
  },
  
  getChangelog: async (skip: number = 0, limit: number = 50) => {
    const params = new URLSearchParams({ skip: String(skip), limit: String(limit) })
    return fetcher(`/v1/changelog?${params}`)
  },
  
  getFeed: async () => {
    return fetcher('/v1/feed.json')
  },
  
  // Events API
  getEvents: async (params?: {
    tier?: string
    signpost_id?: number
    needs_review?: boolean
    source_type?: string
    start_date?: string
    end_date?: string
    skip?: number
    limit?: number
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.tier) searchParams.append('tier', params.tier)
    if (params?.signpost_id) searchParams.append('signpost_id', String(params.signpost_id))
    if (params?.needs_review !== undefined) searchParams.append('needs_review', String(params.needs_review))
    if (params?.source_type) searchParams.append('source_type', params.source_type)
    if (params?.start_date) searchParams.append('start_date', params.start_date)
    if (params?.end_date) searchParams.append('end_date', params.end_date)
    if (params?.skip) searchParams.append('skip', String(params.skip))
    if (params?.limit) searchParams.append('limit', String(params.limit))
    return fetcher(`/v1/events?${searchParams}`)
  },
  
  getEvent: async (id: number) => {
    return fetcher(`/v1/events/${id}`)
  },
  
  getEventsFeed: async () => {
    return fetcher('/v1/events/feed.json')
  },
  
  getRoadmapComparison: async (params?: {
    signpost_code?: string
    roadmap?: string
  }) => {
    const searchParams = new URLSearchParams()
    if (params?.signpost_code) searchParams.append('signpost_code', params.signpost_code)
    if (params?.roadmap) searchParams.append('roadmap', params.roadmap)
    return fetcher(`/v1/roadmaps/compare?${searchParams}`)
  },
  
  approveEvent: async (id: number, token?: string) => {
    const baseUrl = getApiBaseUrl()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['X-API-Key'] = token  // SECURITY FIX: Use X-API-Key (backend expects this, not Bearer)
    }
    const response = await fetch(`${baseUrl}/v1/admin/events/${id}/approve`, {
      method: 'POST',
      headers,
    })
    if (!response.ok) {
      throw new Error(`Failed to approve event: ${response.statusText}`)
    }
    return response.json()
  },
  
  rejectEvent: async (id: number, reason?: string, token?: string) => {
    const baseUrl = getApiBaseUrl()
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    if (token) {
      headers['X-API-Key'] = token  // SECURITY FIX: Use X-API-Key (backend expects this, not Bearer)
    }
    const response = await fetch(`${baseUrl}/v1/admin/events/${id}/reject`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ reason }),
    })
    if (!response.ok) {
      throw new Error(`Failed to reject event: ${response.statusText}`)
    }
    return response.json()
  },
}

