import useSWR from 'swr'
import { fetcher } from '@/lib/api'

export interface IndexData {
  as_of_date: string
  overall: number
  capabilities: number
  agents: number
  inputs: number
  security: number
  safety_margin: number
  preset: string
  confidence_bands: {
    [key: string]: { lower: number; upper: number }
  }
  insufficient: {
    overall: boolean
    categories: {
      capabilities: boolean
      agents: boolean
      inputs: boolean
      security: boolean
    }
  }
}

export function useIndex(preset: string = 'equal', date?: string) {
  const params = new URLSearchParams({ preset })
  if (date) params.append('date', date)
  
  const { data, error, isLoading } = useSWR<IndexData>(
    `/v1/index?${params}`,
    fetcher,
    { refreshInterval: 60000 } // Refresh every minute
  )
  
  return {
    data,
    isLoading,
    isError: error,
  }
}

