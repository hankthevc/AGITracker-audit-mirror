'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import Link from 'next/link'
import useSWR from 'swr'

interface Event {
  id: number
  title: string
  date: string
  tier: string
  source_url?: string
  signpost_links?: Array<{
    signpost_code: string
    signpost_title: string
  }>
}

const TIER_BADGES = {
  A: { label: 'Tier A', class: 'bg-green-100 text-green-800 border-green-300' },
  B: { label: 'Tier B', class: 'bg-blue-100 text-blue-800 border-blue-300' },
  C: { label: 'Tier C', class: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  D: { label: 'Tier D', class: 'bg-gray-100 text-gray-800 border-gray-300' },
}

export function ThisWeeksMovesStrip() {
  const sevenDaysAgo = new Date()
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
  
  const { data, error, isLoading } = useSWR(
    '/v1/events/recent',
    () => apiClient.getEvents({
      start_date: sevenDaysAgo.toISOString().split('T')[0],
      limit: 5,
    })
  )

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">This Week's Moves</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading recent events...</div>
        </CardContent>
      </Card>
    )
  }

  if (error || !data?.items?.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-xl">This Week's Moves</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            No events recorded in the past 7 days.{' '}
            <Link href="/events" className="text-primary hover:underline">
              View all events →
            </Link>
          </div>
        </CardContent>
      </Card>
    )
  }

  const events: Event[] = data.items

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">This Week's Moves</CardTitle>
          <Link
            href="/events"
            className="text-sm text-primary hover:underline font-medium"
          >
            View all →
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {events.map((event) => {
            const tierInfo = TIER_BADGES[event.tier as keyof typeof TIER_BADGES] || TIER_BADGES.D
            return (
              <div
                key={event.id}
                className="border rounded-lg p-3 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`inline-block px-2 py-0.5 text-xs font-medium rounded border ${tierInfo.class}`}
                      >
                        {tierInfo.label}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(event.date)}
                      </span>
                    </div>
                    <Link
                      href={`/events/${event.id}`}
                      className="font-medium text-sm hover:text-primary transition-colors"
                    >
                      {event.title}
                    </Link>
                    {event.signpost_links && event.signpost_links.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {event.signpost_links.slice(0, 2).map((link) => (
                          <span
                            key={link.signpost_code}
                            className="inline-block px-1.5 py-0.5 text-xs bg-slate-100 text-slate-700 rounded"
                          >
                            {link.signpost_code}
                          </span>
                        ))}
                        {event.signpost_links.length > 2 && (
                          <span className="inline-block px-1.5 py-0.5 text-xs text-slate-500">
                            +{event.signpost_links.length - 2} more
                          </span>
                        )}
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
                      className="text-xs text-primary hover:underline flex-shrink-0"
                    >
                      Source ↗
                    </a>
                    </>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

