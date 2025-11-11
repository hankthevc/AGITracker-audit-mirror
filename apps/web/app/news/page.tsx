'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import Link from 'next/link'
import useSWR from 'swr'

interface Event {
  id: number
  title: string
  summary?: string
  date: string
  tier: string
  source_type: string
  source_url?: string
  signpost_links?: Array<{
    signpost_code: string
    signpost_title: string
  }>
}

const TIER_CONFIG = {
  A: { 
    label: 'Tier A', 
    class: 'bg-green-100 text-green-800 border-green-300',
    badge: 'Peer-Reviewed',
    moves_gauges: true
  },
  B: { 
    label: 'Tier B', 
    class: 'bg-blue-100 text-blue-800 border-blue-300',
    badge: 'Official Lab',
    moves_gauges: true
  },
  C: { 
    label: 'Tier C', 
    class: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    badge: 'Reputable Press',
    moves_gauges: false
  },
  D: { 
    label: 'Tier D', 
    class: 'bg-gray-100 text-gray-800 border-gray-300',
    badge: 'Social Media',
    moves_gauges: false
  },
}

function NewsContent() {
  const searchParams = useSearchParams()
  const tierFilter = searchParams.get('tier')
  const sourceTypeFilter = searchParams.get('source_type')
  const linkedFilter = searchParams.get('linked')
  
  const { data, error, isLoading } = useSWR(
    `/v1/events?tier=${tierFilter || ''}&source_type=${sourceTypeFilter || ''}&limit=50`,
    () => apiClient.getEvents({
      tier: tierFilter || undefined,
      source_type: sourceTypeFilter || undefined,
      limit: 50,
    })
  )
  
  // Client-side filter for linked/unlinked
  const allEvents: Event[] = data?.items || []
  const events: Event[] = allEvents.filter((e: Event) => {
    if (linkedFilter === 'yes') return e.signpost_links && e.signpost_links.length > 0
    if (linkedFilter === 'no') return !e.signpost_links || e.signpost_links.length === 0
    return true
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">AI News & Research</h1>
        <p className="text-muted-foreground mb-4">
          Real-time developments mapped to AGI signposts, categorized by evidence quality.
        </p>
        
        {/* Feed Links */}
        <div className="flex items-center gap-4 text-sm">
          <span className="font-medium">Data Feeds:</span>
          <a
            href="/v1/events/feed.json"
            className="text-primary hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            JSON (Public - A/B only) ↗
          </a>
          <a
            href="/v1/events/feed.json?include_research=true"
            className="text-primary hover:underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            JSON (Research - All tiers) ↗
          </a>
        </div>
      </div>

      {/* Evidence Policy Banner */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <h3 className="font-semibold mb-2">Evidence Policy</h3>
          <div className="text-sm space-y-1">
            <p><strong>Tier A (Peer-Reviewed) & Tier B (Official Labs):</strong> Move main gauges directly when mapped to signposts.</p>
            <p><strong>Tier C (Press) & Tier D (Social):</strong> Tracked as "If true" analysis only. Do NOT move gauges.</p>
            <p>See <Link href="/methodology" className="text-primary hover:underline">methodology</Link> for full details.</p>
          </div>
        </CardContent>
      </Card>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <Link
          href="/news"
          className={`px-3 py-1.5 text-sm rounded border transition-colors ${
            !tierFilter
              ? 'bg-primary text-white border-primary'
              : 'bg-white hover:bg-slate-50 border-slate-300'
          }`}
        >
          All News
        </Link>
        {Object.entries(TIER_CONFIG).map(([tier, config]) => (
          <Link
            key={tier}
            href={`/news?tier=${tier}`}
            className={`px-3 py-1.5 text-sm rounded border transition-colors ${
              tierFilter === tier
                ? config.class
                : 'bg-white hover:bg-slate-50 border-slate-300'
            }`}
          >
            {config.label} - {config.badge}
          </Link>
        ))}
         {/* Source type filter */}
         <span className="mx-2 text-muted-foreground">|</span>
         {['news','paper','blog','leaderboard','gov'].map((t) => (
           <Link
             key={t}
             href={`/news?${tierFilter ? `tier=${tierFilter}&` : ''}source_type=${t}`}
             className={`px-3 py-1.5 text-sm rounded border transition-colors ${
               sourceTypeFilter === t
                 ? 'bg-slate-800 text-white border-slate-800'
                 : 'bg-white hover:bg-slate-50 border-slate-300'
             }`}
           >
             {t}
           </Link>
         ))}
         {/* Linked/unlinked filter */}
         <span className="mx-2 text-muted-foreground">|</span>
         {[{v:'yes',l:'Linked'},{v:'no',l:'Unlinked'}].map((opt) => (
           <Link
             key={opt.v}
             href={`/news?${tierFilter ? `tier=${tierFilter}&` : ''}linked=${opt.v}`}
             className={`px-3 py-1.5 text-sm rounded border transition-colors ${
               linkedFilter === opt.v
                 ? 'bg-indigo-600 text-white border-indigo-600'
                 : 'bg-white hover:bg-slate-50 border-slate-300'
             }`}
           >
             {opt.l}
           </Link>
         ))}
        </div>

      {/* Events List */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading news...</p>
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Failed to load news. Please try again later.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && events.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground text-center">
              No news found{tierFilter ? ` for tier ${tierFilter}` : ''}.
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && events.length > 0 && (
        <div className="space-y-4">
          {events.map((event) => {
            const tierInfo = TIER_CONFIG[event.tier as keyof typeof TIER_CONFIG]
            const isIfTrue = !tierInfo.moves_gauges

            return (
              <Card key={event.id} className="hover:shadow-md transition-shadow">
                <CardContent className="pt-6">
                  {/* If True Banner */}
                  {isIfTrue && (
                    <div className="mb-3 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded text-sm">
                      <strong className="text-yellow-800">⚠️ "If True" Analysis:</strong>
                      <span className="text-yellow-700 ml-2">
                        This {event.tier === 'C' ? 'press report' : 'social media post'} does NOT move main gauges. 
                        Tracked for research purposes only.
                      </span>
                    </div>
                  )}

                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`inline-block px-2 py-0.5 text-xs font-medium rounded border ${tierInfo.class}`}>
                          {tierInfo.label}
                        </span>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(event.date)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {event.source_type}
                        </span>
                      </div>

                      <Link
                        href={`/events/${event.id}`}
                        className="text-lg font-semibold hover:text-primary transition-colors block mb-2"
                      >
                        {event.title}
                      </Link>

                      {event.summary && (
                        <p className="text-sm text-muted-foreground mb-2">
                          {event.summary}
                        </p>
                      )}

                      {event.signpost_links && event.signpost_links.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          <span className="text-xs text-muted-foreground">Mapped to:</span>
                          {event.signpost_links.map((link) => (
                            <Link
                              key={link.signpost_code}
                              href={`/signposts/${link.signpost_code}`}
                              className="inline-block px-2 py-1 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded transition-colors"
                            >
                              {link.signpost_code}
                            </Link>
                          ))}
                        </div>
                      )}
                    </div>

                    {event.source_url && (
                      <>
                        {/* eslint-disable-next-line no-restricted-syntax */}
                        {/* Database-sourced URL with noopener/noreferrer */}
                      <a
                        href={event.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline flex-shrink-0"
                      >
                        Source ↗
                      </a>
                      </>
                    )}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default function NewsPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <NewsContent />
    </Suspense>
  )
}

