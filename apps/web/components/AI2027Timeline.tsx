"use client"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { useState } from "react"

interface TimelineItem {
  id: string
  label: string
  signpost_code: string
  target_date: string  // YYYY-MM-DD
  confidence: string  // 'high' | 'medium' | 'low'
  rationale: string
  observed_date?: string  // YYYY-MM-DD if achieved
  current_value?: number
  status: 'ahead' | 'on_track' | 'behind' | 'pending'
}

interface AI2027TimelineProps {
  items: TimelineItem[]
}

export function AI2027Timeline({ items }: AI2027TimelineProps) {
  const [selectedItem, setSelectedItem] = useState<TimelineItem | null>(null)

  // Sort by target date
  const sortedItems = [...items].sort((a, b) => 
    a.target_date.localeCompare(b.target_date)
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ahead':
        return 'bg-green-500'
      case 'on_track':
        return 'bg-blue-500'
      case 'behind':
        return 'bg-red-500'
      case 'pending':
      default:
        return 'bg-gray-400'
    }
  }

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'ahead':
        return 'default'
      case 'on_track':
        return 'secondary'
      case 'behind':
        return 'destructive'
      default:
        return 'outline'
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' })
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'ahead':
        return '🟢 Ahead'
      case 'on_track':
        return '🔵 On Track'
      case 'behind':
        return '🔴 Behind'
      case 'pending':
      default:
        return '⚪ Pending'
    }
  }

  return (
    <div className="space-y-6">
      {/* Timeline visualization */}
      <div className="relative pl-12">
        {sortedItems.map((item, idx) => (
          <div 
            key={item.id} 
            className="relative pb-10 last:pb-0"
            data-testid={`timeline-item-${item.id}`}
          >
            {/* Connector line */}
            {idx < sortedItems.length - 1 && (
              <div 
                className="absolute left-0 top-8 w-0.5 h-full bg-border"
                style={{ marginLeft: '15px' }}
              />
            )}
            
            {/* Timeline dot */}
            <div className="flex items-start gap-6">
              <div 
                className={`w-8 h-8 rounded-full border-4 border-background flex items-center justify-center ${getStatusColor(item.status)}`}
              />
              
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-semibold">{item.label}</h3>
                    <p className="text-sm text-muted-foreground">
                      Target: {formatDate(item.target_date)}
                      {item.observed_date && (
                        <> • Observed: {formatDate(item.observed_date)}</>
                      )}
                    </p>
                  </div>
                  <Badge 
                    variant={getStatusBadgeVariant(item.status)}
                    data-testid={`status-${item.status}`}
                  >
                    {getStatusLabel(item.status)}
                  </Badge>
                </div>
                
                <Card className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setSelectedItem(item)}>
                  <CardContent className="p-4">
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {item.rationale}
                    </p>
                    {item.current_value !== undefined && (
                      <p className="text-sm font-medium mt-2">
                        Current: {(item.current_value * 100).toFixed(1)}%
                      </p>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Evidence modal */}
      {selectedItem && (
        <div 
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedItem(null)}
        >
          <Card className="max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="text-2xl font-bold">{selectedItem.label}</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Signpost: {selectedItem.signpost_code}
                  </p>
                </div>
                <button 
                  onClick={() => setSelectedItem(null)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  ✕
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold mb-2">Prediction</h3>
                  <p className="text-sm text-muted-foreground">{selectedItem.rationale}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="font-semibold mb-1">Target Date</h3>
                    <p className="text-sm">{formatDate(selectedItem.target_date)}</p>
                  </div>
                  {selectedItem.observed_date && (
                    <div>
                      <h3 className="font-semibold mb-1">Observed Date</h3>
                      <p className="text-sm">{formatDate(selectedItem.observed_date)}</p>
                    </div>
                  )}
                </div>

                <div>
                  <h3 className="font-semibold mb-1">Confidence</h3>
                  <Badge variant="outline" className="capitalize">
                    {selectedItem.confidence}
                  </Badge>
                </div>

                <div>
                  <h3 className="font-semibold mb-1">Status</h3>
                  <Badge variant={getStatusBadgeVariant(selectedItem.status)}>
                    {getStatusLabel(selectedItem.status)}
                  </Badge>
                </div>

                {selectedItem.current_value !== undefined && (
                  <div>
                    <h3 className="font-semibold mb-1">Current Progress</h3>
                    <p className="text-sm">{(selectedItem.current_value * 100).toFixed(1)}%</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

