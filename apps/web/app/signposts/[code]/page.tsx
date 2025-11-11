'use client'

/**
 * Signpost Detail Page
 * Shows signpost information with recent incidents and forecast summary
 */

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { Card } from '@/components/ui/card'
import { SignpostBadge } from '@/components/SignpostBadge'
import { SeverityChip } from '@/components/SeverityChip'
import Link from 'next/link'

interface SignpostDetail {
  code: string
  name: string
  category: string | null
  description: string | null
  why_matters: string | null
  measurement_methodology: string | null
  methodology_url: string | null
  counts: {
    forecasts: number
    incidents: number
  }
  recent_incidents: Array<{
    id: number
    title: string
    occurred_at: string
    severity: number
  }>
  forecast_summary: {
    count: number
    earliest: string
    latest: string
    sources: string[]
  } | null
}

export default function SignpostDetailPage() {
  const params = useParams()
  const code = params.code as string
  const [signpost, setSignpost] = useState<SignpostDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch(`/v1/signposts/${code}`)
        if (!res.ok) throw new Error('Not found')
        const data = await res.json()
        setSignpost(data)
      } catch (err) {
        console.error('Failed to load signpost:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [code])

  if (loading) {
    return <div className="container" style={{padding:'var(--space-4)'}}>Loading...</div>
  }

  if (!signpost) {
    return <div className="container" style={{padding:'var(--space-4)'}}>Signpost not found</div>
  }

  return (
    <div className="container" style={{padding:'var(--space-4) 0'}}>
      <div style={{marginBottom:'var(--space-4)'}}>
        <div style={{display:'flex', gap:'var(--space-2)', alignItems:'center', marginBottom:'var(--space-2)'}}>
          <SignpostBadge code={signpost.code} />
          <span style={{color:'var(--muted)', fontSize:'.9rem'}}>{signpost.category}</span>
        </div>
        <h1>{signpost.name}</h1>
        {signpost.description && <p style={{color:'var(--muted)', marginTop:'var(--space-2)'}}>{signpost.description}</p>}
      </div>

      <div style={{display:'grid', gridTemplateColumns:'2fr 1fr', gap:'var(--space-4)', marginTop:'var(--space-4)'}}>
        <div>
          {signpost.why_matters && (
            <Card style={{padding:'var(--space-3)', marginBottom:'var(--space-3)'}}>
              <h2 style={{fontSize:'var(--step-1)', marginBottom:'var(--space-2)'}}>Why This Matters</h2>
              <p style={{lineHeight:1.6}}>{signpost.why_matters}</p>
            </Card>
          )}

          {signpost.measurement_methodology && (
            <Card style={{padding:'var(--space-3)'}}>
              <h2 style={{fontSize:'var(--step-1)', marginBottom:'var(--space-2)'}}>Measurement</h2>
              <p style={{lineHeight:1.6}}>{signpost.measurement_methodology}</p>
            </Card>
          )}
        </div>

        <div>
          <Card style={{padding:'var(--space-3)', marginBottom:'var(--space-3)'}}>
            <h3 style={{fontSize:'var(--step-0)', marginBottom:'var(--space-2)'}}>Activity</h3>
            <div style={{display:'grid', gap:'var(--space-2)'}}>
              <div style={{display:'flex', justifyContent:'space-between'}}>
                <span style={{color:'var(--muted)'}}>Forecasts</span>
                <Link href={`/forecasts?signpost=${code}`} style={{color:'var(--brand)', textDecoration:'none'}}>
                  {signpost.counts.forecasts}
                </Link>
              </div>
              <div style={{display:'flex', justifyContent:'space-between'}}>
                <span style={{color:'var(--muted)'}}>Incidents</span>
                <Link href={`/incidents?signpost=${code}`} style={{color:'var(--brand)', textDecoration:'none'}}>
                  {signpost.counts.incidents}
                </Link>
              </div>
            </div>
          </Card>

          {signpost.recent_incidents.length > 0 && (
            <Card style={{padding:'var(--space-3)'}}>
              <h3 style={{fontSize:'var(--step-0)', marginBottom:'var(--space-2)'}}>Recent Incidents</h3>
              <div style={{display:'grid', gap:'var(--space-2)'}}>
                {signpost.recent_incidents.slice(0, 5).map(inc => (
                  <div key={inc.id} style={{paddingBottom:'var(--space-2)', borderBottom:'1px solid var(--border)'}}>
                    <div style={{display:'flex', gap:'var(--space-2)', alignItems:'center', marginBottom:'.25rem'}}>
                      <SeverityChip value={inc.severity as any} />
                      <span style={{fontSize:'.75rem', color:'var(--muted)'}}>{new Date(inc.occurred_at).toLocaleDateString()}</span>
                    </div>
                    <p style={{fontSize:'.85rem', margin:0}}>{inc.title}</p>
                  </div>
                ))}
              </div>
              {signpost.recent_incidents.length > 5 && (
                <Link href={`/incidents?signpost=${code}`} style={{fontSize:'.85rem', color:'var(--brand)', marginTop:'var(--space-2)', display:'block'}}>
                  View all {signpost.counts.incidents} incidents →
                </Link>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
