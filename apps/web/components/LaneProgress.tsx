'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatPercent } from '@/lib/utils'

interface Lane {
  label: string
  value: number
  confidenceBand?: { lower: number; upper: number }
}

interface LaneProgressProps {
  lanes: Lane[]
}

export function LaneProgress({ lanes }: LaneProgressProps) {
  const getColor = (val: number) => {
    if (val < 0.3) return 'bg-green-500'
    if (val < 0.6) return 'bg-yellow-500'
    return 'bg-red-500'
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {lanes.map((lane) => (
          <div key={lane.label} className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">{lane.label}</span>
              <span 
                className="text-sm font-bold" 
                data-testid={`${lane.label.toLowerCase()}-value`}
              >
                {formatPercent(lane.value)}
              </span>
            </div>
            <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
              {/* Uncertainty band (lighter shade) */}
              {lane.confidenceBand && (
                <div
                  className={`absolute h-full ${getColor(lane.value)} opacity-30`}
                  style={{
                    left: `${lane.confidenceBand.lower * 100}%`,
                    width: `${(lane.confidenceBand.upper - lane.confidenceBand.lower) * 100}%`,
                  }}
                />
              )}
              {/* Main progress bar */}
              <div
                className={`h-full ${getColor(lane.value)} transition-all duration-500`}
                style={{ width: `${lane.value * 100}%` }}
              />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

