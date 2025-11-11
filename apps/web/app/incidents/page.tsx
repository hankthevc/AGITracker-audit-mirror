'use client'

/**
 * Incidents Page - AI Safety Incident Tracker
 * 
 * Displays timeline of AI safety incidents, jailbreaks, and misuses
 * with filtering by severity, vector type, and date range.
 */

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SafeLink } from '@/lib/SafeLink'

interface Incident {
  id: number
  occurred_at: string
  title: string
  description: string | null
  severity: number
  vectors: string[] | null
  signpost_codes: string[] | null
  external_url: string | null
  source: string | null
  created_at: string
}

const SEVERITY_LABELS: Record<number, string> = {
  1: 'Info',
  2: 'Low',
  3: 'Medium',
  4: 'High',
  5: 'Critical'
}

const SEVERITY_COLORS: Record<number, string> = {
  1: 'bg-gray-100 text-gray-700',
  2: 'bg-blue-100 text-blue-700',
  3: 'bg-yellow-100 text-yellow-700',
  4: 'bg-orange-100 text-orange-700',
  5: 'bg-red-100 text-red-700'
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [severityFilter, setSeverityFilter] = useState<number | null>(null)
  const [vectorFilter, setVectorFilter] = useState<string>('')

  useEffect(() => {
    async function loadIncidents() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
        const params = new URLSearchParams()
        if (severityFilter) params.set('severity', severityFilter.toString())
        if (vectorFilter) params.set('vector', vectorFilter)
        
        const response = await fetch(`${apiUrl}/v1/incidents?${params.toString()}`)
        
        if (!response.ok) {
          throw new Error('Failed to load incidents')
        }
        
        const data = await response.json()
        setIncidents(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load incidents')
      } finally {
        setLoading(false)
      }
    }
    
    loadIncidents()
  }, [severityFilter, vectorFilter])

  const exportCSV = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      const params = new URLSearchParams({ format: 'csv' })
      if (severityFilter) params.set('severity', severityFilter.toString())
      if (vectorFilter) params.set('vector', vectorFilter)
      
      const response = await fetch(`${apiUrl}/v1/incidents?${params.toString()}`)
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `incidents_${new Date().toISOString().split('T')[0]}.csv`
      a.click()
    } catch (err) {
      console.error('Export failed:', err)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="text-center text-muted-foreground">Loading incidents...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Card className="p-6 border-red-200 bg-red-50">
          <div className="text-red-600">Error: {error}</div>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">AI Safety Incidents</h1>
            <p className="text-muted-foreground mt-2">
              Timeline of jailbreaks, misuses, and safety failures
            </p>
          </div>
          <Button onClick={exportCSV} variant="outline">
            💾 Export CSV
          </Button>
        </div>

        {/* Filters */}
        <Card className="p-4">
          <div className="flex gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Severity</label>
              <select
                value={severityFilter || ''}
                onChange={(e) => setSeverityFilter(e.target.value ? parseInt(e.target.value) : null)}
                className="border rounded px-3 py-2"
              >
                <option value="">All</option>
                {[1, 2, 3, 4, 5].map(sev => (
                  <option key={sev} value={sev}>{SEVERITY_LABELS[sev]}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Vector</label>
              <input
                type="text"
                placeholder="e.g., jailbreak"
                value={vectorFilter}
                onChange={(e) => setVectorFilter(e.target.value)}
                className="border rounded px-3 py-2"
              />
            </div>
          </div>
        </Card>

        {/* Incidents Table */}
        <div className="space-y-2">
          {incidents.length === 0 && (
            <Card className="p-6 text-center text-muted-foreground">
              No incidents found matching your filters
            </Card>
          )}
          
          {incidents.map(incident => (
            <Card key={incident.id} className="p-4">
              <div className="flex gap-4">
                <div className="flex-shrink-0">
                  <Badge className={SEVERITY_COLORS[incident.severity]}>
                    {SEVERITY_LABELS[incident.severity]}
                  </Badge>
                </div>
                
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold">{incident.title}</h3>
                      <div className="text-sm text-muted-foreground">
                        {new Date(incident.occurred_at).toLocaleDateString('en-US', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                        {incident.source && ` • ${incident.source}`}
                      </div>
                    </div>
                    {incident.external_url && (
                      <SafeLink
                        href={incident.external_url}
                        className="text-sm text-blue-600 hover:underline"
                      >
                        View Source →
                      </SafeLink>
                    )}
                  </div>
                  
                  {incident.description && (
                    <p className="text-sm mt-2">{incident.description}</p>
                  )}
                  
                  {incident.vectors && incident.vectors.length > 0 && (
                    <div className="flex gap-2 mt-2">
                      {incident.vectors.map(vector => (
                        <Badge key={vector} variant="outline">
                          {vector}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

