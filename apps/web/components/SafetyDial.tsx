'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatPercent } from '@/lib/utils'

interface SafetyDialProps {
  safetyMargin: number
}

export function SafetyDial({ safetyMargin }: SafetyDialProps) {
  // Safety margin ranges from -1 to +1
  // Negative = capability sprint outpacing security (red)
  // Positive = security ahead (green)
  
  const clampedMargin = Math.max(-1, Math.min(1, safetyMargin))
  const isNegative = clampedMargin < 0
  const absMargin = Math.abs(clampedMargin)
  
  return (
    <Card data-testid="safety-dial" className={`border-2 ${isNegative ? 'border-red-500' : 'border-green-500'}`}>
      <CardHeader>
        <CardTitle>Safety Margin</CardTitle>
        <CardDescription>Security - Capabilities</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center p-6">
        <div className="relative w-48 h-48 mb-4">
          <svg viewBox="0 0 200 200" className="w-full h-full">
            {/* Background circle */}
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="20"
            />
            {/* Colored arc */}
            <circle
              cx="100"
              cy="100"
              r="80"
              fill="none"
              stroke={isNegative ? 'rgb(239, 68, 68)' : 'rgb(34, 197, 94)'}
              strokeWidth="20"
              strokeDasharray={`${absMargin * 502} 502`}
              transform="rotate(-90 100 100)"
            />
            {/* Center text */}
            <text
              x="100"
              y="100"
              textAnchor="middle"
              dominantBaseline="middle"
              className="text-3xl font-bold fill-current"
              fill={isNegative ? 'rgb(239, 68, 68)' : 'rgb(34, 197, 94)'}
              data-testid="safety-margin"
            >
              {formatPercent(clampedMargin)}
            </text>
          </svg>
        </div>
        <div className={`text-center font-semibold ${isNegative ? 'text-red-600' : 'text-green-600'}`}>
          {isNegative ? '⚠️ Capability Sprint' : '✓ Security Leading'}
        </div>
        <p className="text-sm text-muted-foreground mt-2 text-center max-w-xs">
          {isNegative 
            ? 'Capabilities are advancing faster than security readiness'
            : 'Security measures are keeping pace with capability advancement'}
        </p>
      </CardContent>
    </Card>
  )
}

