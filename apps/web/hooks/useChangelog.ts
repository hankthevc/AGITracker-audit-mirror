import useSWR from 'swr'
import { fetcher } from '@/lib/api'

export interface ChangelogEntry {
  id: number
  occurred_at: string
  type: string
  title: string
  body?: string
  reason?: string
}

export interface ChangelogResponse {
  total: number
  skip: number
  limit: number
  results: ChangelogEntry[]
}

export function useChangelog(limit: number = 5) {
  const { data, error, isLoading } = useSWR<ChangelogResponse>(
    `/v1/changelog?limit=${limit}`,
    fetcher,
    { refreshInterval: 300000 } // Refresh every 5 minutes
  )
  
  return {
    data,
    isLoading,
    isError: error,
  }
}

