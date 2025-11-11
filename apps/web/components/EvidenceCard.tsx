'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { formatDate } from '@/lib/utils'
import { SafeLink } from '@/lib/SafeLink'

interface EvidenceCardProps {
  id: number
  title: string
  summary: string
  metricName: string
  metricValue: number
  unit: string
  observedAt: string
  source: {
    url: string
    domain: string
    type: string
    credibility: 'A' | 'B' | 'C' | 'D'
  }
  extractionConfidence?: number
  retracted?: boolean
}

export function EvidenceCard({
  id,
  title,
  summary,
  metricName,
  metricValue,
  unit,
  observedAt,
  source,
  extractionConfidence,
  retracted = false,
}: EvidenceCardProps) {
  const tierColors = {
    A: 'bg-green-600 text-white',
    B: 'bg-blue-600 text-white',
    C: 'bg-yellow-600 text-white',
    D: 'bg-red-600 text-white',
  }
  
  const tierLabels = {
    A: 'Primary Evidence',
    B: 'Official Lab',
    C: 'Reputable Press',
    D: 'Social Media',
  }
  
  return (
    <Card
      className={`${retracted ? 'opacity-60 border-destructive' : ''} hover:shadow-lg transition-shadow`}
      data-testid={`evidence-card-${id}`}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <CardTitle className={`text-lg ${retracted ? 'line-through' : ''}`}>
            {title}
          </CardTitle>
          <Badge
            className={tierColors[source.credibility]}
            data-testid={`evidence-tier-${source.credibility}`}
          >
            {source.credibility}
          </Badge>
        </div>
        <CardDescription>{tierLabels[source.credibility]}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {retracted && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
            <p className="text-sm text-destructive font-medium">⚠️ This claim has been retracted</p>
          </div>
        )}
        
        <p className="text-sm">{summary}</p>
        
        <div className="bg-muted p-4 rounded-md">
          <div className="text-2xl font-bold">
            {metricValue} {unit}
          </div>
          <div className="text-sm text-muted-foreground">{metricName}</div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-muted-foreground">Source</div>
            <SafeLink
              href={source.url}
              className="text-primary hover:underline truncate block"
            >
              {source.domain}
            </SafeLink>
          </div>
          <div>
            <div className="text-muted-foreground">Observed</div>
            <div>{formatDate(observedAt)}</div>
          </div>
        </div>
        
        {extractionConfidence !== undefined && (
          <div className="text-xs text-muted-foreground">
            Extraction confidence: {(extractionConfidence * 100).toFixed(0)}%
          </div>
        )}
      </CardContent>
    </Card>
  )
}

