'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import { formatDate } from '@/lib/utils'
import Link from 'next/link'
import useSWR, { mutate } from 'swr'

interface Event {
  id: number
  title: string
  summary?: string
  date: string
  tier: string
  source_url?: string
  confidence_score?: number
  signpost_links?: Array<{
    signpost_code: string
    signpost_title: string
    confidence_score?: number
  }>
}

const TIER_BADGES = {
  A: { label: 'Tier A', class: 'bg-green-100 text-green-800 border-green-300' },
  B: { label: 'Tier B', class: 'bg-blue-100 text-blue-800 border-blue-300' },
  C: { label: 'Tier C', class: 'bg-yellow-100 text-yellow-800 border-yellow-300' },
  D: { label: 'Tier D', class: 'bg-gray-100 text-gray-800 border-gray-300' },
}

export default function AdminReviewPage() {
  const [processingEventIds, setProcessingEventIds] = useState<Set<number>>(new Set())
  const [rejectReason, setRejectReason] = useState<{ [key: number]: string }>({})

  const { data, error, isLoading } = useSWR(
    '/v1/events/review',
    () => apiClient.getEvents({ needs_review: true, limit: 50 })
  )

  const events: Event[] = data?.items || []

  const handleApprove = async (eventId: number) => {
    if (processingEventIds.has(eventId)) return

    setProcessingEventIds(new Set([...processingEventIds, eventId]))
    try {
      await apiClient.approveEvent(eventId)
      await mutate('/v1/events/review')
      alert('Event approved successfully!')
    } catch (err) {
      console.error('Failed to approve event:', err)
      alert('Failed to approve event. Please try again.')
    } finally {
      setProcessingEventIds((prev) => {
        const next = new Set(prev)
        next.delete(eventId)
        return next
      })
    }
  }

  const handleReject = async (eventId: number) => {
    if (processingEventIds.has(eventId)) return

    const reason = rejectReason[eventId]
    if (!reason || reason.trim() === '') {
      alert('Please provide a rejection reason.')
      return
    }

    setProcessingEventIds(new Set([...processingEventIds, eventId]))
    try {
      await apiClient.rejectEvent(eventId, reason)
      await mutate('/v1/events/review')
      setRejectReason((prev) => {
        const next = { ...prev }
        delete next[eventId]
        return next
      })
      alert('Event rejected successfully!')
    } catch (err) {
      console.error('Failed to reject event:', err)
      alert('Failed to reject event. Please try again.')
    } finally {
      setProcessingEventIds((prev) => {
        const next = new Set(prev)
        next.delete(eventId)
        return next
      })
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">Event Review Queue</h1>
        <p className="text-muted-foreground">
          Review events that require manual approval before they're linked to signposts.
        </p>
      </div>

      {/* Info */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6 text-sm">
          <p className="mb-2">
            <strong>Review Criteria:</strong> Events with confidence scores below 60% are flagged for manual review.
            Consider the following when approving:
          </p>
          <ul className="list-disc list-inside space-y-1 text-muted-foreground">
            <li>Does the event actually relate to the mapped signposts?</li>
            <li>Is the source credible and the information accurate?</li>
            <li>Is the date and tier classification correct?</li>
            <li>Are there any duplicate or overlapping events?</li>
          </ul>
        </CardContent>
      </Card>

      {/* Events list */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading events...</p>
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">Failed to load review queue. Please try again later.</p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && events.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground text-center">
              No events pending review. Great job! 🎉
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !error && events.length > 0 && (
        <div className="space-y-6">
          <p className="text-sm text-muted-foreground">
            {events.length} event{events.length !== 1 ? 's' : ''} pending review
          </p>
          {events.map((event) => {
            const tierInfo = TIER_BADGES[event.tier as keyof typeof TIER_BADGES] || TIER_BADGES.D
            const isProcessing = processingEventIds.has(event.id)

            return (
              <Card key={event.id}>
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <span className={`inline-block px-2 py-1 text-xs font-medium rounded border ${tierInfo.class}`}>
                      {tierInfo.label}
                    </span>
                    <span className="text-sm text-muted-foreground">{formatDate(event.date)}</span>
                    {event.confidence_score !== undefined && (
                      <span className="text-xs text-muted-foreground">
                        Confidence: {(event.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <CardTitle className="text-lg mt-2">
                    <Link href={`/events/${event.id}`} className="hover:text-primary">
                      {event.title}
                    </Link>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {event.summary && (
                    <p className="text-sm text-muted-foreground">{event.summary}</p>
                  )}

                  {event.source_url && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Source:</p>
                      {/* eslint-disable-next-line no-restricted-syntax */}
                      {/* Database-sourced URL (A/B tier evidence) with noopener/noreferrer */}
                      <a
                        href={event.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline break-all"
                      >
                        {event.source_url} ↗
                      </a>
                    </div>
                  )}

                  {event.signpost_links && event.signpost_links.length > 0 && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Proposed signpost mappings:</p>
                      <div className="space-y-2">
                        {event.signpost_links.map((link) => (
                          <div key={link.signpost_code} className="border rounded p-2 text-sm">
                            <div className="flex items-center justify-between">
                              <div>
                                <Link
                                  href={`/signposts/${link.signpost_code}`}
                                  className="font-medium text-primary hover:underline"
                                >
                                  {link.signpost_code}
                                </Link>
                                <p className="text-xs text-muted-foreground mt-0.5">{link.signpost_title}</p>
                              </div>
                              {link.confidence_score !== undefined && (
                                <span className="text-xs text-muted-foreground">
                                  {(link.confidence_score * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Rejection reason input */}
                  <div>
                    <label htmlFor={`reject-reason-${event.id}`} className="text-xs text-muted-foreground block mb-1">
                      Rejection reason (optional):
                    </label>
                    <textarea
                      id={`reject-reason-${event.id}`}
                      value={rejectReason[event.id] || ''}
                      onChange={(e) =>
                        setRejectReason({ ...rejectReason, [event.id]: e.target.value })
                      }
                      className="w-full px-3 py-2 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-primary"
                      rows={2}
                      placeholder="e.g., 'Source not credible', 'Duplicate of event #123', 'Incorrect signpost mapping'"
                      disabled={isProcessing}
                    />
                  </div>

                  {/* Action buttons */}
                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={() => handleApprove(event.id)}
                      disabled={isProcessing}
                      className="flex-1 px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isProcessing ? 'Processing...' : 'Approve'}
                    </button>
                    <button
                      onClick={() => handleReject(event.id)}
                      disabled={isProcessing}
                      className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      {isProcessing ? 'Processing...' : 'Reject'}
                    </button>
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

