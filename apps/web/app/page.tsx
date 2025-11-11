'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { CompositeGauge } from '@/components/CompositeGauge'
import { LaneProgress } from '@/components/LaneProgress'
import { SafetyDial } from '@/components/SafetyDial'
import { PresetSwitcher } from '@/components/PresetSwitcher'
import { ChangelogPanel } from '@/components/ChangelogPanel'
import { ThisWeeksMovesStrip } from '@/components/ThisWeeksMovesStrip'
import { HistoricalIndexChart } from '@/components/HistoricalIndexChart'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useIndex } from '@/hooks/useIndex'
import { formatDate } from '@/lib/utils'
import { getApiBaseUrl } from '@/lib/apiBase'

function HomeContent() {
  const searchParams = useSearchParams()
  const preset = searchParams.get('preset') || 'equal'
  const [showErrorDetails, setShowErrorDetails] = useState(false)
  
  const { data, isLoading, isError } = useIndex(preset)
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading index data...</p>
        </div>
      </div>
    )
  }
  
  if (isError || !data) {
    const apiUrl = getApiBaseUrl()
    const errorMessage = isError?.message || 'Unknown error'
    const errorStatus = isError?.status || 'N/A'
    const errorDetail = isError?.detail || errorMessage
    
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="border-destructive max-w-2xl">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Data</CardTitle>
            <CardDescription>
              Unable to fetch index data from{' '}
              <code className="text-xs">{apiUrl}/v1/index</code>
              {errorStatus !== 'N/A' && (
                <span className="block mt-2">
                  <strong>Status:</strong> {errorStatus}
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Make sure the API server is running. Visit{' '}
              <a href="/_debug" className="text-primary hover:underline">
                /_debug
              </a>{' '}
              for connectivity details.
            </p>
            <button
              onClick={() => setShowErrorDetails(!showErrorDetails)}
              className="text-sm text-primary hover:underline"
              data-testid="error-details-toggle"
            >
              {showErrorDetails ? '▼ Hide details' : '▶ Show details'}
            </button>
            {showErrorDetails && (
              <pre className="mt-2 p-3 bg-muted rounded text-xs overflow-auto max-h-40">
                {errorDetail}
              </pre>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }
  
  const lanes = [
    {
      label: 'Capabilities',
      value: data.capabilities,
      confidenceBand: data.confidence_bands?.capabilities,
    },
    {
      label: 'Agents',
      value: data.agents,
      confidenceBand: data.confidence_bands?.agents,
    },
    {
      label: 'Inputs',
      value: data.inputs,
      confidenceBand: data.confidence_bands?.inputs,
    },
    {
      label: 'Security',
      value: data.security,
      confidenceBand: data.confidence_bands?.security,
    },
  ]
  
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">AGI Signpost Tracker</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Evidence-first dashboard tracking proximity to AGI via measurable signposts
        </p>
        <div className="flex justify-center">
          <PresetSwitcher />
        </div>
        <p className="text-sm text-muted-foreground">
          As of {formatDate(data.as_of_date)} • Preset: <span className="font-medium capitalize">{preset}</span>
        </p>
      </div>
      
      {/* Main gauge and safety dial */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <CompositeGauge
          value={data.overall}
          label="Overall AGI Proximity"
          description="Harmonic mean of capabilities and inputs"
          insufficient={data.insufficient?.overall}
        />
        <SafetyDial safetyMargin={data.safety_margin} />
      </div>
      
      {/* Category progress lanes */}
      <LaneProgress lanes={lanes} />
      
      {/* Inputs Sparkline */}
      <Card data-testid="inputs-sparkline">
        <CardHeader>
          <CardTitle className="text-base">Inputs Progress Trend</CardTitle>
          <CardDescription>Recent changes in training compute, DC power, and algorithmic efficiency</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            {/* Simple sparkline visualization */}
            <div className="flex-1 flex items-end gap-1 h-12">
              {[0.15, 0.18, 0.20, 0.22, 0.25].map((value, idx) => (
                <div
                  key={idx}
                  className="flex-1 bg-blue-500 rounded-t"
                  style={{ height: `${value * 100}%` }}
                  title={`${(value * 100).toFixed(1)}%`}
                />
              ))}
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{(data.inputs * 100).toFixed(1)}%</div>
              <div className="text-xs text-muted-foreground">Current</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            Tracking FLOPs milestones (1e25 → 1e27), DC power (0.1 → 10 GW), and algorithmic efficiency gains.
            <a href="/compute" className="text-primary hover:underline ml-1">View details →</a>
          </div>
        </CardContent>
      </Card>
      
      {/* What moved this week */}
      <ThisWeeksMovesStrip />
      
      {/* Historical Progress Chart */}
      <HistoricalIndexChart preset={preset} height={350} />
      
      {/* Recent changelog */}
      <ChangelogPanel />
      
      {/* Explanation */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>Understanding the Dashboard</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            <strong>Overall Proximity:</strong> Tracks progress toward a general-purpose AI that can autonomously
            perform the majority of economically valuable remote cognitive tasks at median professional quality.
          </p>
          <p>
            <strong>Safety Margin:</strong> Difference between security readiness and capability advancement.
            Negative values (red) indicate capabilities are outpacing security measures.
          </p>
          <p>
            <strong>Evidence Tiers:</strong> A = peer-reviewed/leaderboard (primary), B = lab blog (official),
            C = reputable press, D = social media. Only A/B evidence moves the main gauges.
          </p>
          <p>
            <a href="/methodology" className="text-primary font-medium hover:underline">
              Read full methodology →
            </a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function Home() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <HomeContent />
    </Suspense>
  )
}

