'use client'

/**
 * What-If Simulator - Interactive weight adjustment for Progress Index
 * 
 * Allows users to:
 * - Adjust category weights with sliders
 * - Select from expert presets (Equal, Aschenbrenner, Cotra, Conservative)
 * - See real-time diff vs baseline
 * - Share via URL parameters
 * - Export simulated vs baseline data
 */

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { Label } from './ui/label'
import { Select } from './ui/select'

interface CategoryWeights {
  capabilities: number
  agents: number
  inputs: number
  security: number
  economic?: number
  research?: number
  geopolitical?: number
  safety_incidents?: number
}

interface SimulationResult {
  simulated: {
    value: number
    components: Record<string, number>
  }
  baseline: {
    value: number
    components: Record<string, number>
  }
  diff: {
    value_diff: number
    component_diffs: Record<string, number>
  }
}

// Core 4 categories used in main index calculation
const CORE_CATEGORIES = ['capabilities', 'agents', 'inputs', 'security'] as const

const PRESETS: Record<string, CategoryWeights> = {
  equal: {
    capabilities: 0.25,
    agents: 0.25,
    inputs: 0.25,
    security: 0.25,
  },
  aschenbrenner: {
    capabilities: 0.2,
    agents: 0.3,
    inputs: 0.4,
    security: 0.1,
  },
  cotra: {
    capabilities: 0.3,
    agents: 0.35,
    inputs: 0.25,
    security: 0.1,
  },
  conservative: {
    capabilities: 0.15,
    agents: 0.15,
    inputs: 0.3,
    security: 0.4, // Conservative weights security heavily
  },
}

const PRESET_LABELS: Record<string, string> = {
  equal: 'Equal Weights',
  aschenbrenner: 'Aschenbrenner (AGI by 2027)',
  cotra: 'Cotra (Bioanchors)',
  conservative: 'Conservative (Safety-First)',
}

export function WhatIfSimulator() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // Initialize weights from URL or default to equal
  const getInitialWeights = (): CategoryWeights => {
    const urlWeights = searchParams.get('weights')
    if (urlWeights) {
      try {
        return JSON.parse(decodeURIComponent(urlWeights))
      } catch {
        return PRESETS.equal
      }
    }
    return PRESETS.equal
  }

  const [weights, setWeights] = useState<CategoryWeights>(getInitialWeights)
  const [selectedPreset, setSelectedPreset] = useState<string>('equal')
  const [simulation, setSimulation] = useState<SimulationResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Run simulation when weights change
  const runSimulation = useCallback(async (newWeights: CategoryWeights) => {
    setLoading(true)
    setError(null)
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/v1/index/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ weights: newWeights }),
      })
      
      if (!response.ok) {
        throw new Error('Failed to run simulation')
      }
      
      const result: SimulationResult = await response.json()
      setSimulation(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Simulation failed')
    } finally {
      setLoading(false)
    }
  }, [])

  // Update weights and URL
  const updateWeights = useCallback((newWeights: CategoryWeights, preset?: string) => {
    setWeights(newWeights)
    if (preset) {
      setSelectedPreset(preset)
    }
    
    // Update URL with new weights (shareable link)
    const params = new URLSearchParams()
    params.set('weights', encodeURIComponent(JSON.stringify(newWeights)))
    if (preset) {
      params.set('preset', preset)
    }
    router.push(`?${params.toString()}`, { scroll: false })
    
    // Run simulation with new weights
    runSimulation(newWeights)
  }, [router, runSimulation])

  // Handle preset selection
  const handlePresetChange = (preset: string) => {
    const presetWeights = PRESETS[preset]
    if (presetWeights) {
      updateWeights(presetWeights, preset)
    }
  }

  // Handle slider change
  const handleSliderChange = (category: keyof CategoryWeights, value: number) => {
    const newWeights = { ...weights, [category]: value }
    updateWeights(newWeights, 'custom')
  }

  // Normalize weights to sum to 1.0
  const normalizeWeights = () => {
    const sum = CORE_CATEGORIES.reduce((total, cat) => total + (weights[cat] || 0), 0)
    if (sum === 0) return
    
    const normalized = CORE_CATEGORIES.reduce((acc, cat) => {
      acc[cat] = (weights[cat] || 0) / sum
      return acc
    }, {} as CategoryWeights)
    
    updateWeights(normalized, 'custom')
  }

  // Export simulation data
  const exportData = (format: 'json' | 'csv') => {
    if (!simulation) return
    
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(simulation, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `whatif-simulation-${new Date().toISOString().split('T')[0]}.json`
      a.click()
    } else {
      // CSV format
      const rows = [
        ['Category', 'Simulated', 'Baseline', 'Diff'],
        ...CORE_CATEGORIES.map(cat => [
          cat,
          simulation.simulated.components[cat]?.toFixed(2) || '0.00',
          simulation.baseline.components[cat]?.toFixed(2) || '0.00',
          simulation.diff.component_diffs[cat]?.toFixed(2) || '0.00',
        ]),
        ['Overall', 
          simulation.simulated.value.toFixed(2),
          simulation.baseline.value.toFixed(2),
          simulation.diff.value_diff.toFixed(2)
        ],
      ]
      
      const csv = rows.map(row => row.join(',')).join('\n')
      const blob = new Blob([csv], { type: 'text/csv' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `whatif-simulation-${new Date().toISOString().split('T')[0]}.csv`
      a.click()
    }
  }

  // Copy shareable link
  const copyLink = () => {
    const url = window.location.href
    navigator.clipboard.writeText(url)
    // Could add toast notification here
  }

  // Initial simulation on mount
  useEffect(() => {
    runSimulation(weights)
  }, []) // Run once on mount only

  const totalWeight = CORE_CATEGORIES.reduce((sum, cat) => sum + (weights[cat] || 0), 0)
  const isNormalized = Math.abs(totalWeight - 1.0) < 0.01

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">What-If Simulator</h2>
          <p className="text-muted-foreground">
            Adjust weights to see how different prioritization scenarios affect the Progress Index
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={copyLink} variant="outline" size="sm">
            📋 Copy Link
          </Button>
          <Button onClick={() => exportData('csv')} variant="outline" size="sm">
            💾 Export CSV
          </Button>
          <Button onClick={() => exportData('json')} variant="outline" size="sm">
            💾 Export JSON
          </Button>
        </div>
      </div>

      {/* Preset Selector */}
      <Card className="p-6">
        <div className="space-y-4">
          <div>
            <Label htmlFor="preset-select" className="text-base font-semibold">
              Expert Presets
            </Label>
            <p className="text-sm text-muted-foreground mb-2">
              Load weights from well-known AGI timeline scenarios
            </p>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {Object.entries(PRESET_LABELS).map(([key, label]) => (
              <Button
                key={key}
                onClick={() => handlePresetChange(key)}
                variant={selectedPreset === key ? 'default' : 'outline'}
                className="w-full"
              >
                {label}
              </Button>
            ))}
          </div>
        </div>
      </Card>

      {/* Weight Sliders */}
      <Card className="p-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label className="text-base font-semibold">Category Weights</Label>
              <p className="text-sm text-muted-foreground">
                Adjust how much each dimension contributes to the overall index
              </p>
            </div>
            <div className="text-right">
              <div className={`text-sm font-medium ${isNormalized ? 'text-green-600' : 'text-amber-600'}`}>
                Total: {totalWeight.toFixed(2)}
              </div>
              {!isNormalized && (
                <Button onClick={normalizeWeights} variant="link" size="sm" className="h-auto p-0">
                  Normalize to 1.0
                </Button>
              )}
            </div>
          </div>

          <div className="space-y-6">
            {CORE_CATEGORIES.map((category) => (
              <div key={category} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor={`slider-${category}`} className="capitalize">
                    {category}
                  </Label>
                  <span className="text-sm font-mono">
                    {((weights[category] || 0) * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  id={`slider-${category}`}
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={weights[category] || 0}
                  onChange={(e) => handleSliderChange(category, parseFloat(e.target.value))}
                  className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Results */}
      {loading && (
        <Card className="p-6">
          <div className="text-center text-muted-foreground">
            Running simulation...
          </div>
        </Card>
      )}

      {error && (
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="text-red-600">
            Error: {error}
          </div>
        </Card>
      )}

      {simulation && !loading && (
        <Card className="p-6">
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-4">Simulation Results</h3>
              
              {/* Overall Comparison */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Baseline (Equal)</div>
                  <div className="text-2xl font-bold">
                    {(simulation.baseline.value * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Your Scenario</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {(simulation.simulated.value * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-sm text-muted-foreground mb-1">Difference</div>
                  <div className={`text-2xl font-bold ${
                    simulation.diff.value_diff > 0 ? 'text-green-600' : 
                    simulation.diff.value_diff < 0 ? 'text-red-600' : 
                    'text-gray-600'
                  }`}>
                    {simulation.diff.value_diff > 0 ? '+' : ''}
                    {(simulation.diff.value_diff * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Component Breakdown */}
              <div>
                <h4 className="text-sm font-semibold mb-3">Component Breakdown</h4>
                <div className="space-y-2">
                  {CORE_CATEGORIES.map((category) => {
                    const diff = simulation.diff.component_diffs[category] || 0
                    return (
                      <div key={category} className="flex items-center justify-between text-sm">
                        <span className="capitalize">{category}</span>
                        <div className="flex items-center gap-4">
                          <span className="text-muted-foreground">
                            {((simulation.baseline.components[category] || 0) * 100).toFixed(1)}%
                          </span>
                          <span className="font-medium">→</span>
                          <span className="font-medium">
                            {((simulation.simulated.components[category] || 0) * 100).toFixed(1)}%
                          </span>
                          <span className={`font-mono w-16 text-right ${
                            diff > 0 ? 'text-green-600' : diff < 0 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {diff > 0 ? '+' : ''}{(diff * 100).toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Methodology Note */}
      <Card className="p-6 bg-gray-50 dark:bg-gray-900">
        <h4 className="text-sm font-semibold mb-2">About the Simulation</h4>
        <p className="text-sm text-muted-foreground">
          The Progress Index uses a <strong>harmonic mean</strong> of capabilities and inputs, 
          which means both dimensions must advance together. Weights determine how much each category 
          contributes before aggregation. The baseline uses equal weights (25% each) for comparison.
        </p>
      </Card>
    </div>
  )
}

