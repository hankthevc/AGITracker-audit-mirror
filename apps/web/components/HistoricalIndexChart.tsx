'use client'

import { useEffect, useState, useMemo, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Download, ZoomIn, ZoomOut } from 'lucide-react'
import { getApiBaseUrl } from '@/lib/apiBase'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceDot,
} from 'recharts'

const API_URL = getApiBaseUrl()

interface HistoryDataPoint {
  date: string
  overall: number
  capabilities: number
  agents: number
  inputs: number
  security: number
  events: Array<{ id: number; title: string; tier: string }>
}

interface HistoryResponse {
  preset: string
  days: number
  start_date: string
  end_date: string
  history: HistoryDataPoint[]
}

const ZOOM_LEVELS = [
  { label: '1M', days: 30 },
  { label: '3M', days: 90 },
  { label: '6M', days: 180 },
  { label: '1Y', days: 365 },
]

const PRESET_COLORS = {
  equal: '#3b82f6',      // blue
  aschenbrenner: '#f59e0b', // amber
  ai2027: '#10b981',     // green
}

interface ChartProps {
  preset?: string
  height?: number
}

export function HistoricalIndexChart({ 
  preset = 'equal', 
  height = 400
}: ChartProps) {
  const [data, setData] = useState<HistoryResponse | null>(null)
  const [comparisonData, setComparisonData] = useState<Record<string, HistoryResponse>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [zoomLevel, setZoomLevel] = useState(90) // Default 3 months
  const [showCategories, setShowCategories] = useState(false)
  const [showComparison, setShowComparison] = useState(false)
  
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true)
      setError(null)
      
      try {
        const res = await fetch(`${API_URL}/v1/index/history?preset=${preset}&days=${zoomLevel}`)
        
        if (!res.ok) {
          throw new Error('Failed to fetch historical data')
        }
        
        const json = await res.json()
        setData(json)
        
        // Fetch comparison presets if enabled
        if (showComparison) {
          const comparisons: Record<string, HistoryResponse> = {}
          const otherPresets = ['equal', 'aschenbrenner', 'ai2027'].filter(p => p !== preset)
          
          for (const p of otherPresets) {
            try {
              const compRes = await fetch(`${API_URL}/v1/index/history?preset=${p}&days=${zoomLevel}`)
              if (compRes.ok) {
                comparisons[p] = await compRes.json()
              }
            } catch {
              // Silently fail for comparisons
            }
          }
          
          setComparisonData(comparisons)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data')
      } finally {
        setIsLoading(false)
      }
    }
    
    fetchData()
  }, [preset, zoomLevel, showComparison])
  
  // Memoized event handlers
  const downloadPNG = useCallback(() => {
    // This is a simplified version - would need html2canvas or similar for full implementation
    alert('PNG download feature requires additional canvas library setup')
  }, [])
  
  const handleZoomChange = useCallback((days: number) => {
    setZoomLevel(days)
  }, [])
  
  const toggleCategories = useCallback(() => {
    setShowCategories(prev => !prev)
  }, [])
  
  const toggleComparison = useCallback(() => {
    setShowComparison(prev => !prev)
  }, [])
  
  // ✅ FIX: Proper typing instead of 'any'
  interface ChartDataPoint {
    date: string
    [key: string]: string | number // Dynamic keys for presets and categories
  }
  
  // ✅ OPTIMIZATION: Memoize chart data transformation (MOVED BEFORE EARLY RETURNS TO FIX HOOKS ERROR)
  const chartData = useMemo(() => {
    if (!data) return []
    
    return data.history.map(point => {
      const item: ChartDataPoint = {
        date: new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        [preset]: point.overall * 100,
      }
      
      if (showCategories) {
        item.capabilities = point.capabilities * 100
        item.agents = point.agents * 100
        item.inputs = point.inputs * 100
        item.security = point.security * 100
      }
      
      // Add comparison presets
      if (showComparison) {
        Object.entries(comparisonData).forEach(([p, compData]) => {
          const compPoint = compData.history.find(h => h.date === point.date)
          if (compPoint) {
            item[p] = compPoint.overall * 100
          }
        })
      }
      
      return item
    })
  }, [data, preset, showCategories, showComparison, comparisonData])
  
  // ✅ OPTIMIZATION: Memoize events filtering (MOVED BEFORE EARLY RETURNS TO FIX HOOKS ERROR)
  const eventsWithDates = useMemo(() => {
    if (!data) return []
    return data.history
      .filter(point => point.events && point.events.length > 0)
      .slice(-5) // Show only last 5 event dates
  }, [data])

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Historical Progress</CardTitle>
        </CardHeader>
        <CardContent className="h-96 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading historical data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }
  
  if (error || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Historical Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-destructive/10 text-destructive rounded-lg">
            {error || 'No data available'}
          </div>
        </CardContent>
      </Card>
    )
  }
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Historical Progress</CardTitle>
            <CardDescription>
              AGI Proximity Index over time ({data.start_date} to {data.end_date})
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={downloadPNG}
              aria-label="Download chart as PNG image"
            >
              <Download className="w-4 h-4 mr-2" aria-hidden="true" />
              PNG
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Zoom Controls */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex gap-2" role="group" aria-label="Chart time range controls">
            {ZOOM_LEVELS.map(level => (
              <Button
                key={level.days}
                variant={zoomLevel === level.days ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleZoomChange(level.days)}
                aria-label={`Show last ${level.label}`}
                aria-pressed={zoomLevel === level.days}
              >
                {level.label}
              </Button>
            ))}
          </div>
          
          <div className="flex gap-2" role="group" aria-label="Chart display options">
            <Button
              variant={showCategories ? 'default' : 'outline'}
              size="sm"
              onClick={toggleCategories}
              aria-label="Toggle category breakdown view"
              aria-pressed={showCategories}
            >
              Categories
            </Button>
            <Button
              variant={showComparison ? 'default' : 'outline'}
              size="sm"
              onClick={toggleComparison}
              aria-label="Toggle comparison with other presets"
              aria-pressed={showComparison}
            >
              Compare
            </Button>
          </div>
        </div>
        
        {/* Chart */}
        <ResponsiveContainer width="100%" height={height}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="date" 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="#6b7280"
              style={{ fontSize: '12px' }}
              domain={[0, 100]}
              label={{ value: 'Progress (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: '#ffffff', 
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
              }}
              formatter={(value: number) => `${value.toFixed(1)}%`}
            />
            <Legend />
            
            {/* Main preset line */}
            <Line
              type="monotone"
              dataKey={preset}
              name={preset.charAt(0).toUpperCase() + preset.slice(1)}
              stroke={PRESET_COLORS[preset as keyof typeof PRESET_COLORS]}
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6 }}
            />
            
            {/* Category lines */}
            {showCategories && (
              <>
                <Line
                  type="monotone"
                  dataKey="capabilities"
                  name="Capabilities"
                  stroke="#ef4444"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="agents"
                  name="Agents"
                  stroke="#8b5cf6"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="inputs"
                  name="Inputs"
                  stroke="#f59e0b"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="security"
                  name="Security"
                  stroke="#10b981"
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  dot={false}
                />
              </>
            )}
            
            {/* Comparison lines */}
            {showComparison && Object.keys(comparisonData).map(p => (
              <Line
                key={p}
                type="monotone"
                dataKey={p}
                name={p.charAt(0).toUpperCase() + p.slice(1)}
                stroke={PRESET_COLORS[p as keyof typeof PRESET_COLORS]}
                strokeWidth={2}
                strokeDasharray="3 3"
                dot={false}
              />
            ))}
            
            {/* Event annotations */}
            {eventsWithDates.map((point, idx) => {
              const chartPoint = chartData.find(d => d.date === new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }))
              if (!chartPoint || !point.events[0]) return null
              
              return (
                <ReferenceDot
                  key={idx}
                  x={chartPoint.date}
                  y={chartPoint[preset]}
                  r={8}
                  fill={point.events[0].tier === 'A' ? '#10b981' : '#3b82f6'}
                  stroke="#fff"
                  strokeWidth={2}
                />
              )
            })}
          </LineChart>
        </ResponsiveContainer>
        
        {/* Recent Events */}
        {eventsWithDates.length > 0 && (
          <div className="mt-6 pt-6 border-t">
            <h4 className="text-sm font-semibold mb-3">Recent Milestone Events</h4>
            <div className="flex flex-wrap gap-2">
              {eventsWithDates.map((point, idx) => 
                point.events.slice(0, 1).map(event => (
                  <Badge key={`${idx}-${event.id}`} variant={event.tier === 'A' ? 'default' : 'secondary'}>
                    {new Date(point.date).toLocaleDateString()}: {event.title.slice(0, 40)}...
                  </Badge>
                ))
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

