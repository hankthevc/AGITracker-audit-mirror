/**
 * KPI Card component for dashboard.
 * 
 * Displays a key metric with value, delta, and optional sparkline.
 */

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { KpiCard as KpiCardType, TimePoint } from '@/lib/types/dashboard'

interface KpiCardProps {
  kpi: KpiCardType
  className?: string
}

export function KpiCard({ kpi, className = '' }: KpiCardProps) {
  const getDeltaIcon = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined || delta === 0) {
      return <Minus className="h-4 w-4 text-gray-400" />
    }
    if (delta > 0) {
      return <TrendingUp className="h-4 w-4 text-green-600" />
    }
    return <TrendingDown className="h-4 w-4 text-red-600" />
  }

  const getDeltaColor = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined || delta === 0) return 'text-gray-600'
    return delta > 0 ? 'text-green-600' : 'text-red-600'
  }

  const formatDelta = (delta: number | null | undefined) => {
    if (delta === null || delta === undefined) return null
    const sign = delta > 0 ? '+' : ''
    return `${sign}${delta.toFixed(1)}%`
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {kpi.label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline justify-between">
          <div className="text-3xl font-bold">{kpi.value}</div>
          {kpi.deltaPct !== undefined && kpi.deltaPct !== null && (
            <div className={`flex items-center gap-1 text-sm font-medium ${getDeltaColor(kpi.deltaPct)}`}>
              {getDeltaIcon(kpi.deltaPct)}
              <span>{formatDelta(kpi.deltaPct)}</span>
            </div>
          )}
        </div>
        
        {/* Tiny sparkline (if trend data provided) */}
        {kpi.trend && kpi.trend.length > 0 && (
          <div className="mt-4 h-12 flex items-end gap-0.5">
            {kpi.trend.map((point, i) => {
              const values = kpi.trend!.map(p => p.v)
              const min = Math.min(...values)
              const max = Math.max(...values)
              const range = max - min || 1
              const height = ((point.v - min) / range) * 100
              
              return (
                <div
                  key={i}
                  className="flex-1 bg-blue-500/30 rounded-sm transition-all hover:bg-blue-500/50"
                  style={{ height: `${height}%` }}
                  title={`${point.t}: ${point.v}`}
                />
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

