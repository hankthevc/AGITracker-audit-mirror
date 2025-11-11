/**
 * Timeseries Chart component using Recharts.
 * 
 * Renders line/area charts with brush, tooltip, and accessibility features.
 */

'use client'

import { useMemo } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Brush,
  ResponsiveContainer
} from 'recharts'
import { Timeseries } from '@/lib/types/dashboard'

interface TimeseriesChartProps {
  data: Timeseries
  height?: number
  showBrush?: boolean
  variant?: 'line' | 'area'
}

export function TimeseriesChart({
  data,
  height = 300,
  showBrush = false,
  variant = 'area'
}: TimeseriesChartProps) {
  
  const chartData = useMemo(() => {
    return data.series.map(point => ({
      date: new Date(point.t).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      fullDate: point.t,
      value: point.v
    }))
  }, [data.series])

  const formatYAxis = (value: number) => {
    if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`
    if (value >= 1000) return `${(value / 1000).toFixed(1)}K`
    return value.toFixed(0)
  }

  const ChartComponent = variant === 'area' ? AreaChart : LineChart

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ChartComponent
        data={chartData}
        margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
      >
        <defs>
          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
          </linearGradient>
        </defs>
        
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        
        <XAxis
          dataKey="date"
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
        />
        
        <YAxis
          stroke="#6b7280"
          fontSize={12}
          tickLine={false}
          tickFormatter={formatYAxis}
        />
        
        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '8px 12px'
          }}
          labelStyle={{ fontWeight: 600, marginBottom: '4px' }}
          formatter={(value: number) => [value.toFixed(2), data.meta?.label || data.metric]}
        />
        
        {showBrush && (
          <Brush
            dataKey="date"
            height={30}
            stroke="#3b82f6"
            fill="#f3f4f6"
          />
        )}
        
        {variant === 'area' ? (
          <Area
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="url(#colorValue)"
          />
        ) : (
          <Line
            type="monotone"
            dataKey="value"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
          />
        )}
      </ChartComponent>
    </ResponsiveContainer>
  )
}

