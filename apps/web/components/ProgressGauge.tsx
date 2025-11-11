'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { TrendingUp, TrendingDown, Info } from 'lucide-react'

interface ProgressGaugeProps {
  value: number  // 0-100
  components: Record<string, number>
  delta7d?: number
  delta30d?: number
  weights?: Record<string, number>
}

export function ProgressGauge({
  value,
  components,
  delta7d,
  delta30d,
  weights
}: ProgressGaugeProps) {
  const [showExplainer, setShowExplainer] = useState(false)

  const getColor = (val: number) => {
    if (val < 25) return 'text-green-600'
    if (val < 50) return 'text-yellow-600'
    if (val < 75) return 'text-orange-600'
    return 'text-red-600'
  }

  const getGaugeColor = (val: number) => {
    if (val < 25) return 'bg-green-500'
    if (val < 50) return 'bg-yellow-500'
    if (val < 75) return 'bg-orange-500'
    return 'bg-red-500'
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle>AGI Progress Index</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowExplainer(!showExplainer)}
          >
            <Info className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Gauge */}
        <div className="flex flex-col items-center">
          <div className={`text-6xl font-bold ${getColor(value)}`}>
            {value.toFixed(1)}
          </div>
          <div className="text-sm text-muted-foreground">out of 100</div>
          
          {/* Delta Indicators */}
          <div className="flex gap-4 mt-4">
            {delta7d !== undefined && (
              <div className="flex items-center gap-1 text-sm">
                {delta7d >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                <span className={delta7d >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {delta7d >= 0 ? '+' : ''}{delta7d.toFixed(2)}
                </span>
                <span className="text-muted-foreground">7d</span>
              </div>
            )}
            {delta30d !== undefined && (
              <div className="flex items-center gap-1 text-sm">
                {delta30d >= 0 ? (
                  <TrendingUp className="h-4 w-4 text-green-600" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-600" />
                )}
                <span className={delta30d >= 0 ? 'text-green-600' : 'text-red-600'}>
                  {delta30d >= 0 ? '+' : ''}{delta30d.toFixed(2)}
                </span>
                <span className="text-muted-foreground">30d</span>
              </div>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full ${getGaugeColor(value)} transition-all duration-500`}
              style={{ width: `${value}%` }}
            />
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Baseline (0)</span>
            <span>AGI (100)</span>
          </div>
        </div>

        {/* Component Breakdown */}
        <div className="space-y-2">
          <div className="text-sm font-medium">Component Scores</div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            {Object.entries(components).map(([key, score]) => (
              <div key={key} className="flex justify-between">
                <span className="text-muted-foreground capitalize">
                  {key.replace('_', ' ')}
                </span>
                <span className="font-mono">{score.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Explainer Modal */}
        {showExplainer && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
            <h3 className="font-semibold mb-2">How We Compute This Index</h3>
            <p className="text-muted-foreground mb-3">
              The AGI Progress Index combines progress across 8 dimensions using
              first-class signposts with measurable baselines and targets.
            </p>
            
            <div className="mb-3">
              <div className="font-medium mb-1">Weights Used:</div>
              <div className="grid grid-cols-2 gap-1 text-xs">
                {weights && Object.entries(weights).map(([key, weight]) => (
                  <div key={key} className="flex justify-between">
                    <span className="capitalize">{key.replace('_', ' ')}</span>
                    <span className="font-mono">{(weight * 100).toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            </div>
            
            <a
              href="/methodology"
              className="text-primary hover:underline text-xs"
            >
              Learn more about our methodology →
            </a>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

