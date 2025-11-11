'use client'

/**
 * Signposts Directory - Browse all AGI signposts
 */

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { SignpostBadge } from '@/components/SignpostBadge'

interface SignpostItem {
  code: string
  name: string
  category: string | null
  description: string | null
  counts?: {
    forecasts: number
    incidents: number
  }
}

export default function SignpostsPage() {
  const [signposts, setSignposts] = useState<SignpostItem[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch('/v1/signposts?include_counts=true&order=forecasts&limit=200')
        const data = await res.json()
        setSignposts(data.results || [])
      } catch (err) {
        console.error('Failed to load signposts:', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const filtered = signposts.filter(sp => 
    !search || 
    sp.name.toLowerCase().includes(search.toLowerCase()) ||
    sp.code.toLowerCase().includes(search.toLowerCase())
  )

  if (loading) {
    return <div className="container" style={{padding:'var(--space-4)'}}>Loading signposts...</div>
  }

  return (
    <div className="container" style={{padding:'var(--space-4) 0'}}>
      <div style={{marginBottom:'var(--space-4)'}}>
        <h1>Signposts</h1>
        <p style={{color:'var(--muted)', marginTop:'var(--space-2)'}}>
          Measurable milestones tracking AGI progress
        </p>
      </div>

      <Input
        placeholder="Search signposts..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{marginBottom:'var(--space-4)', maxWidth:'400px'}}
      />

      <div style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(300px, 1fr))', gap:'var(--space-3)'}}>
        {filtered.map(sp => (
          <Link key={sp.code} href={`/signposts/${sp.code}`} style={{textDecoration:'none'}}>
            <Card style={{padding:'var(--space-3)', height:'100%', transition:'transform var(--dur-2) var(--ease-2), box-shadow var(--dur-2) var(--ease-2)'}}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'start', marginBottom:'var(--space-2)'}}>
                <h3 style={{fontSize:'var(--step-1)', margin:0}}>{sp.name}</h3>
                <SignpostBadge code={sp.code} />
              </div>
              {sp.description && (
                <p style={{color:'var(--muted)', fontSize:'.9rem', margin:'var(--space-2) 0', lineHeight:1.5}}>
                  {sp.description.substring(0, 150)}{sp.description.length > 150 ? '...' : ''}
                </p>
              )}
              {sp.counts && (
                <div style={{display:'flex', gap:'var(--space-3)', marginTop:'var(--space-2)', fontSize:'.85rem', color:'var(--muted)'}}>
                  <span>{sp.counts.forecasts} forecasts</span>
                  <span>•</span>
                  <span>{sp.counts.incidents} incidents</span>
                </div>
              )}
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}

