'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatPercent } from '@/lib/utils'

interface CompositeGaugeProps {
  value: number
  label?: string
  description?: string
  insufficient?: boolean
}

export function CompositeGauge({ value, label = "Overall Proximity", description, insufficient = false }: CompositeGaugeProps) {
  // Clamp value between 0 and 1
  const clampedValue = Math.max(0, Math.min(1, value))
  
  // Color gradient: green (low) -> yellow -> red (high)
  const getColor = (val: number) => {
    if (val < 0.3) return 'rgb(34, 197, 94)' // green
    if (val < 0.6) return 'rgb(234, 179, 8)' // yellow
    return 'rgb(239, 68, 68)' // red
  }
  
  const color = getColor(clampedValue)
  const rotation = clampedValue * 180 - 90 // -90 to 90 degrees
  
  return (
    <Card data-testid="composite-gauge" className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <CardTitle>{label}</CardTitle>
          <a 
            href="/methodology" 
            className="text-muted-foreground hover:text-primary transition-colors"
            title="Learn about our scoring methodology"
            aria-label="Learn about our scoring methodology"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="18" 
              height="18" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="2" 
              strokeLinecap="round" 
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
          </a>
        </div>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center p-6">
        <div className="relative w-64 h-32 mb-4">
          {/* Background arc */}
          <svg viewBox="0 0 200 100" className="w-full h-full">
            <path
              d="M 10 90 A 90 90 0 0 1 190 90"
              fill="none"
              stroke="#e5e7eb"
              strokeWidth="20"
              strokeLinecap="round"
            />
            {/* Filled arc */}
            <path
              d="M 10 90 A 90 90 0 0 1 190 90"
              fill="none"
              stroke={color}
              strokeWidth="20"
              strokeLinecap="round"
              strokeDasharray={`${clampedValue * 283} 283`}
            />
            {/* Needle */}
            <line
              x1="100"
              y1="90"
              x2="100"
              y2="20"
              stroke="#1f2937"
              strokeWidth="3"
              strokeLinecap="round"
              transform={`rotate(${rotation} 100 90)`}
            />
            <circle cx="100" cy="90" r="5" fill="#1f2937" />
          </svg>
        </div>
        <div className="text-center">
          {insufficient ? (
            <>
              <div 
                className="text-4xl font-bold text-gray-400" 
                data-testid="overall-value"
                title="N/A – Waiting for Inputs/Security data. Overall index requires non-zero values in Inputs and Security categories to compute a meaningful harmonic mean."
              >
                N/A
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                Waiting for Inputs/Security
              </div>
            </>
          ) : (
            <>
              <div className="text-4xl font-bold" style={{ color }} data-testid="overall-value">
                {formatPercent(clampedValue)}
              </div>
              <div className="text-sm text-muted-foreground mt-1">
                {clampedValue < 0.3 ? 'Early Stage' : clampedValue < 0.6 ? 'Progressing' : 'Advanced'}
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

