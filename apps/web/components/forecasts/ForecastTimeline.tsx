'use client'

/**
 * Forecast Timeline Visualization
 * 
 * Displays expert AGI timeline predictions as a strip plot with consensus indicators.
 */

import { useMemo } from 'react'
import { Card } from '../ui/card'
import { Badge } from '../ui/badge'
import type { ConsensusData } from '@/lib/types/forecasts'

interface Props {
  consensus: ConsensusData
}

export function ForecastTimeline({ consensus }: Props) {
  const { signpost_name, forecasts, median_timeline, timeline_spread_days } = consensus
  
  // Calculate timeline range for chart
  const timelineRange = useMemo(() => {
    if (!forecasts.length) return null
    
    const dates = forecasts.map(f => new Date(f.timeline).getTime())
    const min = Math.min(...dates)
    const max = Math.max(...dates)
    const padding = (max - min) * 0.1 // 10% padding
    
    return {
      min: min - padding,
      max: max + padding,
      span: max - min + 2 * padding
    }
  }, [forecasts])
  
  if (!timelineRange || !forecasts.length) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          No forecasts available for this signpost
        </div>
      </Card>
    )
  }
  
  // Position each forecast on the timeline (0-100%)
  const positionedForecasts = forecasts.map(f => {
    const timestamp = new Date(f.timeline).getTime()
    const position = ((timestamp - timelineRange.min) / timelineRange.span) * 100
    return { ...f, position }
  })
  
  // Position median line
  const medianPosition = median_timeline
    ? ((new Date(median_timeline).getTime() - timelineRange.min) / timelineRange.span) * 100
    : null
  
  return (
    <Card className="p-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold">{signpost_name}</h3>
          <p className="text-sm text-muted-foreground">
            {consensus.forecast_count} expert predictions
            {timeline_spread_days && ` • ${Math.round(timeline_spread_days / 365)} year spread`}
          </p>
        </div>
        
        {/* Timeline visualization */}
        <div className="relative h-24 bg-gray-100 dark:bg-gray-800 rounded-lg">
          {/* Median line */}
          {medianPosition !== null && (
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-blue-600"
              style={{ left: `${medianPosition}%` }}
            >
              <div className="absolute -top-6 left-1/2 -translate-x-1/2 text-xs font-medium text-blue-600">
                Median
              </div>
            </div>
          )}
          
          {/* Forecast points */}
          {positionedForecasts.map((f, idx) => (
            <div
              key={f.id}
              className="absolute top-1/2 -translate-y-1/2"
              style={{ left: `${f.position}%` }}
            >
              <div className="relative group">
                <div 
                  className="w-3 h-3 rounded-full border-2 border-white shadow-md cursor-pointer"
                  style={{ 
                    backgroundColor: getSourceColor(f.source),
                    transform: `translateX(-50%) translateY(${(idx % 3 - 1) * 12}px)`
                  }}
                />
                
                {/* Tooltip */}
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 hidden group-hover:block z-10 w-48">
                  <div className="bg-gray-900 text-white text-xs rounded p-2 shadow-lg">
                    <div className="font-semibold">{f.source}</div>
                    <div>{new Date(f.timeline).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}</div>
                    {f.confidence && <div>Confidence: {(f.confidence * 100).toFixed(0)}%</div>}
                    {f.quote && <div className="mt-1 italic">&quot;{f.quote.substring(0, 100)}...&quot;</div>}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Timeline labels */}
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>{new Date(timelineRange.min).getFullYear()}</span>
          {median_timeline && (
            <span className="text-blue-600 font-medium">
              {new Date(median_timeline).toLocaleDateString('en-US', { year: 'numeric', month: 'short' })}
            </span>
          )}
          <span>{new Date(timelineRange.max).getFullYear()}</span>
        </div>
        
        {/* Source legend */}
        <div className="flex flex-wrap gap-2">
          {Array.from(new Set(forecasts.map(f => f.source))).map(source => (
            <Badge key={source} variant="outline" style={{ borderColor: getSourceColor(source) }}>
              <span className="w-2 h-2 rounded-full inline-block mr-1" style={{ backgroundColor: getSourceColor(source) }} />
              {source}
            </Badge>
          ))}
        </div>
      </div>
    </Card>
  )
}

// Simple color mapping for sources
function getSourceColor(source: string): string {
  const colors: Record<string, string> = {
    'Aschenbrenner': '#ef4444', // red
    'Cotra': '#3b82f6', // blue
    'Epoch': '#10b981', // green
    'Conservative': '#f59e0b', // amber
  }
  
  // Check if source contains any of the keys
  for (const [key, color] of Object.entries(colors)) {
    if (source.includes(key)) return color
  }
  
  // Default color based on hash of source name
  const hash = source.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  const hue = hash % 360
  return `hsl(${hue}, 70%, 50%)`
}

