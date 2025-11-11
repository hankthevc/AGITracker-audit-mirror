'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TimeseriesChart } from '@/components/charts/TimeseriesChart'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import useSWR from 'swr'
import { Timeseries, MetricKey } from '@/lib/types/dashboard'

const METRICS: Array<{ key: MetricKey; label: string; description: string }> = [
  { key: 'events_per_day', label: 'Events Per Day', description: 'A/B tier research events published daily' },
  { key: 'swebench_score', label: 'SWE-bench Score', description: 'Software engineering benchmark performance' },
  { key: 'signposts_completed', label: 'Signposts Completed', description: 'Number of signposts with measurable progress' },
  { key: 'safety_incidents_per_month', label: 'Safety Incidents', description: 'Reported safety issues per month' },
]

const WINDOWS = [
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' },
  { value: '1y', label: '1 Year' },
  { value: 'all', label: 'All Time' },
]

export default function ChartsPage() {
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>('events_per_day')
  const [selectedWindow, setSelectedWindow] = useState('30d')
  const [showExplanation, setShowExplanation] = useState(false)

  const { data, isLoading, error } = useSWR<Timeseries>(
    `/v1/dashboard/timeseries?metric=${selectedMetric}&window=${selectedWindow}`,
    async () => {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/v1/dashboard/timeseries?metric=${selectedMetric}&window=${selectedWindow}`
      )
      if (!response.ok) throw new Error('Failed to fetch timeseries')
      return response.json()
    }
  )

  const currentMetric = METRICS.find(m => m.key === selectedMetric)

  const handleExplain = () => {
    setShowExplanation(!showExplanation)
  }

  // Template explanation (Phase 4 will add GPT integration)
  const explanation = {
    paragraph: `The ${currentMetric?.label.toLowerCase() || 'selected metric'} shows ${selectedWindow} of activity tracking AGI development. This data aggregates ${data?.series.length || 0} data points from our evidence database.`,
    bullets: [
      `Tracking ${data?.series.length || 0} data points over ${selectedWindow}`,
      `Based on A/B tier evidence (peer-reviewed papers and official announcements)`,
      `Updated in real-time as new events are published`
    ]
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Charts Explorer</h1>
        <p className="text-xl text-muted-foreground">
          Interactive data visualization and trend analysis
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle>Select Metric & Time Window</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Metric Selector */}
          <div>
            <label className="text-sm font-medium mb-2 block">Metric</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {METRICS.map((metric) => (
                <button
                  key={metric.key}
                  onClick={() => setSelectedMetric(metric.key)}
                  className={`p-4 text-left rounded-lg border-2 transition-all ${
                    selectedMetric === metric.key
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-semibold mb-1">{metric.label}</div>
                  <div className="text-sm text-muted-foreground">{metric.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Window Selector */}
          <div>
            <label className="text-sm font-medium mb-2 block">Time Window</label>
            <div className="flex gap-2 flex-wrap">
              {WINDOWS.map((window) => (
                <button
                  key={window.value}
                  onClick={() => setSelectedWindow(window.value)}
                  className={`px-4 py-2 rounded-md border transition-colors ${
                    selectedWindow === window.value
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  {window.label}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      {isLoading && (
        <Card>
          <CardContent className="h-96 flex items-center justify-center">
            <div className="text-muted-foreground">Loading chart...</div>
          </CardContent>
        </Card>
      )}

      {!isLoading && data && (
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle>{currentMetric?.label || selectedMetric}</CardTitle>
                <p className="text-sm text-muted-foreground mt-1">
                  {currentMetric?.description || ''}
                </p>
              </div>
              <Button onClick={handleExplain} variant="outline" size="sm">
                {showExplanation ? 'Hide' : 'Explain'} Chart
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Explanation (if shown) */}
            {showExplanation && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold mb-2">What This Chart Shows</h3>
                <p className="text-sm mb-3">{explanation.paragraph}</p>
                <ul className="space-y-1">
                  {explanation.bullets.map((bullet, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Chart */}
            <TimeseriesChart data={data} height={400} showBrush={true} variant="area" />
            
            {/* Metadata */}
            <div className="flex gap-2 text-xs text-muted-foreground">
              <Badge variant="outline">{data.series.length} data points</Badge>
              <Badge variant="outline">Window: {selectedWindow}</Badge>
              {data.meta?.generated_at && (
                <Badge variant="outline">
                  Updated: {new Date(data.meta.generated_at as string).toLocaleTimeString()}
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

