'use client'

/**
 * Forecasts Page - Expert AGI Timeline Predictions
 * 
 * Shows consensus forecasts from multiple experts (Aschenbrenner, Cotra, Epoch, etc.)
 * with timeline visualizations and disagreement analysis.
 */

import { useState, useEffect } from 'react'
import { ForecastTimeline } from '@/components/forecasts/ForecastTimeline'
import { Card } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import type { ConsensusData } from '@/lib/types/forecasts'

const CATEGORIES = [
  { value: '', label: 'All Categories' },
  { value: 'capabilities', label: 'Capabilities' },
  { value: 'agents', label: 'Agents' },
  { value: 'inputs', label: 'Inputs' },
  { value: 'security', label: 'Security' },
]

export default function ForecastsPage() {
  const [consensus, setConsensus] = useState<ConsensusData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    async function loadForecasts() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/v1/forecasts/consensus`)
        
        if (!response.ok) {
          throw new Error('Failed to load forecasts')
        }
        
        const data = await response.json()
        setConsensus(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load forecasts')
      } finally {
        setLoading(false)
      }
    }
    
    loadForecasts()
  }, [])

  // Filter consensus data
  const filteredConsensus = consensus.filter(item => {
    const matchesSearch = searchQuery === '' || 
      item.signpost_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.signpost_code.toLowerCase().includes(searchQuery.toLowerCase())
    
    // Note: To filter by category, we'd need to join with signpost data
    // For now, just filter by search
    return matchesSearch
  })

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center text-muted-foreground">
          Loading expert forecasts...
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="text-red-600">Error: {error}</div>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Expert AGI Timeline Forecasts</h1>
          <p className="text-muted-foreground mt-2">
            Aggregated predictions from leading AI researchers and organizations
          </p>
        </div>

        {/* Filters */}
        <Card className="p-4">
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search signposts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </Card>

        {/* Summary Stats */}
        <Card className="p-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold">{consensus.length}</div>
              <div className="text-sm text-muted-foreground">Signposts with Forecasts</div>
            </div>
            <div>
              <div className="text-2xl font-bold">
                {consensus.reduce((sum, c) => sum + c.forecast_count, 0)}
              </div>
              <div className="text-sm text-muted-foreground">Total Predictions</div>
            </div>
            <div>
              <div className="text-2xl font-bold">
                {Array.from(new Set(consensus.flatMap(c => c.forecasts.map(f => f.source)))).length}
              </div>
              <div className="text-sm text-muted-foreground">Expert Sources</div>
            </div>
          </div>
        </Card>

        {/* Forecast Timelines */}
        <div className="space-y-4">
          {filteredConsensus.length === 0 && (
            <Card className="p-6 text-center text-muted-foreground">
              No forecasts match your search criteria
            </Card>
          )}
          
          {filteredConsensus.map(item => (
            <ForecastTimeline key={item.signpost_code} consensus={item} />
          ))}
        </div>

        {/* Methodology Note */}
        <Card className="p-6 bg-gray-50 dark:bg-gray-900">
          <h3 className="text-sm font-semibold mb-2">About These Forecasts</h3>
          <p className="text-sm text-muted-foreground">
            Timeline predictions are extracted from published research, public statements, and 
            forecasting platforms. The <strong>median timeline</strong> represents the consensus 
            estimate across all sources. Spread indicates disagreement/uncertainty. Higher confidence 
            values indicate the expert stated greater certainty in their prediction.
          </p>
        </Card>
      </div>
    </div>
  )
}

