'use client'

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { getApiBaseUrl } from '@/lib/apiBase'
import { Download, Share2, RotateCcw } from 'lucide-react'
import Link from 'next/link'

const API_URL = getApiBaseUrl()

// Preset configurations
const PRESETS = {
  equal: { capabilities: 0.25, agents: 0.25, inputs: 0.25, security: 0.25, name: 'Equal' },
  aschenbrenner: { capabilities: 0.20, agents: 0.30, inputs: 0.40, security: 0.10, name: 'Aschenbrenner' },
  ai2027: { capabilities: 0.30, agents: 0.35, inputs: 0.25, security: 0.10, name: 'AI-2027' },
}

interface WeightState {
  capabilities: number
  agents: number
  inputs: number
  security: number
}

interface IndexResult {
  overall: number
  capabilities: number
  agents: number
  inputs: number
  security: number
  safety_margin: number
  insufficient: {
    overall: boolean
  }
}

export default function CustomPresetPage() {
  const [weights, setWeights] = useState<WeightState>({
    capabilities: 0.25,
    agents: 0.25,
    inputs: 0.25,
    security: 0.25,
  })
  
  const [presetName, setPresetName] = useState('My Custom Preset')
  const [customIndex, setCustomIndex] = useState<IndexResult | null>(null)
  const [comparisonIndexes, setComparisonIndexes] = useState<Record<string, IndexResult>>({})
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Calculate real-time index
  const calculateIndex = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams({
        capabilities: weights.capabilities.toString(),
        agents: weights.agents.toString(),
        inputs: weights.inputs.toString(),
        security: weights.security.toString(),
      })
      
      const res = await fetch(`${API_URL}/v1/index/custom?${params}`)
      
      if (!res.ok) {
        const errorData = await res.json()
        throw new Error(errorData.detail || 'Failed to calculate index')
      }
      
      const data = await res.json()
      setCustomIndex(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate index')
      setCustomIndex(null)
    } finally {
      setIsLoading(false)
    }
  }, [weights])
  
  // Load comparison presets
  useEffect(() => {
    const loadComparisons = async () => {
      const results: Record<string, IndexResult> = {}
      
      for (const [key, preset] of Object.entries(PRESETS)) {
        try {
          const res = await fetch(`${API_URL}/v1/index?preset=${key}`)
          if (res.ok) {
            results[key] = await res.json()
          }
        } catch {
          // Silently fail for comparisons
        }
      }
      
      setComparisonIndexes(results)
    }
    
    loadComparisons()
  }, [])
  
  // Recalculate when weights change
  useEffect(() => {
    const total = weights.capabilities + weights.agents + weights.inputs + weights.security
    
    // Only calculate if weights sum to ~1.0
    if (Math.abs(total - 1.0) < 0.01) {
      calculateIndex()
    } else {
      setCustomIndex(null)
    }
  }, [weights, calculateIndex])
  
  const handleWeightChange = (category: keyof WeightState, value: number) => {
    setWeights(prev => ({
      ...prev,
      [category]: value,
    }))
  }
  
  const handleSliderChange = (category: keyof WeightState, value: string) => {
    const numValue = parseFloat(value) / 100
    handleWeightChange(category, numValue)
  }
  
  const loadPreset = (presetKey: keyof typeof PRESETS) => {
    const preset = PRESETS[presetKey]
    setWeights({
      capabilities: preset.capabilities,
      agents: preset.agents,
      inputs: preset.inputs,
      security: preset.security,
    })
    setPresetName(preset.name)
  }
  
  const resetToEqual = () => {
    loadPreset('equal')
  }
  
  const downloadJSON = () => {
    const data = {
      name: presetName,
      weights,
      calculated: customIndex,
      created_at: new Date().toISOString(),
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${presetName.toLowerCase().replace(/\s+/g, '-')}.json`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  const shareViaURL = () => {
    const params = new URLSearchParams({
      capabilities: weights.capabilities.toString(),
      agents: weights.agents.toString(),
      inputs: weights.inputs.toString(),
      security: weights.security.toString(),
      name: presetName,
    })
    
    const shareUrl = `${window.location.origin}${window.location.pathname}?${params}`
    navigator.clipboard.writeText(shareUrl)
    alert('Share URL copied to clipboard!')
  }
  
  // Load from URL params on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const cap = params.get('capabilities')
    const agents = params.get('agents')
    const inputs = params.get('inputs')
    const security = params.get('security')
    const name = params.get('name')
    
    if (cap && agents && inputs && security) {
      setWeights({
        capabilities: parseFloat(cap),
        agents: parseFloat(agents),
        inputs: parseFloat(inputs),
        security: parseFloat(security),
      })
    }
    
    if (name) {
      setPresetName(name)
    }
  }, [])
  
  const totalWeight = weights.capabilities + weights.agents + weights.inputs + weights.security
  const isValid = Math.abs(totalWeight - 1.0) < 0.01
  
  return (
    <div className="container mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4">Custom Preset Builder</h1>
        <p className="text-lg text-muted-foreground">
          Create your own category weights and see real-time index calculations.
        </p>
      </div>
      
      {/* Preset Name */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Preset Name</CardTitle>
        </CardHeader>
        <CardContent>
          <Input
            value={presetName}
            onChange={(e) => setPresetName(e.target.value)}
            placeholder="My Custom Preset"
            className="max-w-md"
          />
        </CardContent>
      </Card>
      
      {/* Weight Sliders */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Category Weights</CardTitle>
          <CardDescription>
            Adjust the weights for each category. They must sum to 1.0 (100%).
            {!isValid && (
              <span className="text-destructive ml-2">
                Current total: {(totalWeight * 100).toFixed(1)}%
              </span>
            )}
            {isValid && (
              <span className="text-green-600 ml-2">✓ Valid (100%)</span>
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {(['capabilities', 'agents', 'inputs', 'security'] as const).map((category) => (
            <div key={category} className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor={category} className="capitalize text-base font-medium">
                  {category}
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="number"
                    value={(weights[category] * 100).toFixed(1)}
                    onChange={(e) => handleWeightChange(category, parseFloat(e.target.value) / 100)}
                    min="0"
                    max="100"
                    step="1"
                    className="w-20 text-right"
                  />
                  <span className="text-sm text-muted-foreground">%</span>
                </div>
              </div>
              <input
                id={category}
                type="range"
                min="0"
                max="100"
                step="1"
                value={weights[category] * 100}
                onChange={(e) => handleSliderChange(category, e.target.value)}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
            </div>
          ))}
          
          <div className="flex gap-3 pt-4 border-t">
            <Button variant="outline" onClick={resetToEqual} size="sm">
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset to Equal
            </Button>
            <Button variant="outline" onClick={() => loadPreset('aschenbrenner')} size="sm">
              Load Aschenbrenner
            </Button>
            <Button variant="outline" onClick={() => loadPreset('ai2027')} size="sm">
              Load AI-2027
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* Real-time Calculation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card className={!isValid ? 'opacity-50' : ''}>
          <CardHeader>
            <CardTitle>Your Custom Index</CardTitle>
            <CardDescription>
              {isLoading ? 'Calculating...' : isValid ? 'Real-time calculation' : 'Adjust weights to see calculation'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="p-4 bg-destructive/10 text-destructive rounded-lg mb-4">
                {error}
              </div>
            )}
            
            {customIndex && !error && (
              <div className="space-y-4">
                <div className="text-center p-6 bg-blue-50 rounded-lg">
                  <div className="text-sm text-muted-foreground mb-2">Overall AGI Proximity</div>
                  {customIndex.insufficient.overall ? (
                    <div className="text-4xl font-bold text-gray-400">N/A</div>
                  ) : (
                    <div className="text-6xl font-bold text-primary">
                      {(customIndex.overall * 100).toFixed(1)}%
                    </div>
                  )}
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-gray-50 rounded">
                    <div className="text-xs text-muted-foreground">Capabilities</div>
                    <div className="text-lg font-semibold">{(customIndex.capabilities * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded">
                    <div className="text-xs text-muted-foreground">Agents</div>
                    <div className="text-lg font-semibold">{(customIndex.agents * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded">
                    <div className="text-xs text-muted-foreground">Inputs</div>
                    <div className="text-lg font-semibold">{(customIndex.inputs * 100).toFixed(1)}%</div>
                  </div>
                  <div className="p-3 bg-gray-50 rounded">
                    <div className="text-xs text-muted-foreground">Security</div>
                    <div className="text-lg font-semibold">{(customIndex.security * 100).toFixed(1)}%</div>
                  </div>
                </div>
                
                <div className="p-3 border rounded">
                  <div className="text-xs text-muted-foreground">Safety Margin</div>
                  <div className={`text-lg font-semibold ${customIndex.safety_margin < 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {(customIndex.safety_margin * 100).toFixed(1)}%
                    <span className="text-xs ml-2">
                      ({customIndex.safety_margin < 0 ? 'Behind' : 'Ahead'})
                    </span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Comparison View */}
        <Card>
          <CardHeader>
            <CardTitle>Comparison with Standard Presets</CardTitle>
            <CardDescription>How your custom weights compare</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(PRESETS).map(([key, preset]) => {
              const index = comparisonIndexes[key]
              if (!index) return null
              
              const diff = customIndex ? (customIndex.overall - index.overall) * 100 : 0
              
              return (
                <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">{preset.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {(index.overall * 100).toFixed(1)}%
                    </div>
                  </div>
                  {customIndex && (
                    <Badge variant={diff > 0 ? 'default' : diff < 0 ? 'destructive' : 'secondary'}>
                      {diff > 0 ? '+' : ''}{diff.toFixed(1)}%
                    </Badge>
                  )}
                </div>
              )
            })}
          </CardContent>
        </Card>
      </div>
      
      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Save & Share</CardTitle>
          <CardDescription>Download or share your custom preset</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-3">
          <Button onClick={downloadJSON} disabled={!isValid}>
            <Download className="w-4 h-4 mr-2" />
            Download JSON
          </Button>
          <Button onClick={shareViaURL} disabled={!isValid} variant="outline">
            <Share2 className="w-4 h-4 mr-2" />
            Copy Share URL
          </Button>
        </CardContent>
      </Card>
      
      <div className="mt-8 flex justify-center">
        <Link href="/" className="text-primary hover:underline">
          ← Back to Dashboard
        </Link>
      </div>
    </div>
  )
}

