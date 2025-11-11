'use client'

import { Suspense, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { apiClient } from '@/lib/api'
import useSWR from 'swr'
import Link from 'next/link'

interface ForecastDrift {
  signpost_code: string
  signpost_name: string
  category: string
  drifts: {
    [roadmap: string]: {
      status: 'ahead' | 'on_track' | 'behind'
      days_drift: number
      summary: string
    }
  }
}

interface CapabilitySecurityGap {
  alert_level: 'high' | 'medium' | 'low'
  gap_magnitude: number
  summary: string
  recommendations: string[]
  capabilities_score: number
  security_score: number
}

function InsightsContent() {
  const { data: indexData } = useSWR('/v1/index', () => apiClient.getIndex())
  const { data: eventsData } = useSWR('/v1/events?limit=20', () =>
    apiClient.getEvents({ limit: 20 })
  )

  // Mock forecast drift data (would come from API in production)
  const forecastDrifts: ForecastDrift[] = [
    {
      signpost_code: 'swe_bench_85',
      signpost_name: 'SWE-bench Verified 85%',
      category: 'capabilities',
      drifts: {
        aschenbrenner: {
          status: 'on_track',
          days_drift: 15,
          summary: '15 days ahead of Aschenbrenner timeline',
        },
        ai2027: {
          status: 'ahead',
          days_drift: 45,
          summary: '45 days ahead of AI 2027 timeline',
        },
      },
    },
    {
      signpost_code: 'compute_1e26',
      signpost_name: '10^26 FLOP Training Run',
      category: 'inputs',
      drifts: {
        aschenbrenner: {
          status: 'ahead',
          days_drift: 30,
          summary: '30 days ahead of Aschenbrenner timeline',
        },
      },
    },
  ]

  // Calculate capability-security gap
  const capSecurityGap: CapabilitySecurityGap | null = indexData
    ? {
        alert_level:
          indexData.capabilities - indexData.security > 0.3
            ? 'high'
            : indexData.capabilities - indexData.security > 0.2
            ? 'medium'
            : 'low',
        gap_magnitude: indexData.capabilities - indexData.security,
        summary: `Capabilities advancing ${Math.round(
          (indexData.capabilities - indexData.security) * 100
        )}% faster than security measures`,
        recommendations: [
          'Deploy inference monitoring (Security L2)',
          'Implement mandatory safety evaluations',
          'Consider model weight security measures',
        ],
        capabilities_score: indexData.capabilities,
        security_score: indexData.security,
      }
    : null

  const statusColors = {
    ahead: 'bg-green-100 text-green-800 border-green-300',
    on_track: 'bg-blue-100 text-blue-800 border-blue-300',
    behind: 'bg-red-100 text-red-800 border-red-300',
  }

  const alertColors = {
    high: 'bg-red-100 text-red-800 border-red-300',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    low: 'bg-blue-100 text-blue-800 border-blue-300',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">AI-Enabled Insights</h1>
        <p className="text-muted-foreground">
          AI-powered analysis of AGI progress, timeline drift, and security-capability gaps
        </p>
      </div>

      {/* Capability-Security Gap Alert */}
      {capSecurityGap && capSecurityGap.alert_level !== 'low' && (
        <Card className={`border-2 ${alertColors[capSecurityGap.alert_level]}`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">⚠️ Security Gap Alert</CardTitle>
              <Badge className={alertColors[capSecurityGap.alert_level]}>
                {capSecurityGap.alert_level.toUpperCase()}
              </Badge>
            </div>
            <CardDescription>{capSecurityGap.summary}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="text-muted-foreground">Capabilities Score</div>
                  <div className="text-2xl font-bold">
                    {(capSecurityGap.capabilities_score * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-muted-foreground">Security Score</div>
                  <div className="text-2xl font-bold">
                    {(capSecurityGap.security_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              <div>
                <div className="font-medium mb-2">Recommended Actions:</div>
                <ul className="space-y-1 text-sm">
                  {capSecurityGap.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Forecast Drift Analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Forecast Drift Analysis</CardTitle>
          <CardDescription>
            Comparing current progress to roadmap predictions from Aschenbrenner, AI 2027, and
            others
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {forecastDrifts.map((drift) => (
              <div key={drift.signpost_code} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <Link
                      href={`/signposts/${drift.signpost_code}`}
                      className="text-lg font-semibold hover:text-primary transition-colors"
                    >
                      {drift.signpost_name}
                    </Link>
                    <div className="text-sm text-muted-foreground capitalize">
                      {drift.category}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  {Object.entries(drift.drifts).map(([roadmap, driftData]) => (
                    <div
                      key={roadmap}
                      className="flex items-center justify-between text-sm bg-slate-50 p-2 rounded"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-medium capitalize">{roadmap}:</span>
                        <Badge
                          className={`${statusColors[driftData.status]} text-xs`}
                        >
                          {driftData.status.replace('_', ' ')}
                        </Badge>
                      </div>
                      <span className="text-muted-foreground">{driftData.summary}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}

            <div className="text-sm text-muted-foreground mt-4 p-3 bg-blue-50 rounded">
              <strong>Methodology:</strong> Drift calculated using linear interpolation between
              baseline (2023) and predicted target dates. Positive values indicate ahead of
              schedule; negative values indicate behind.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent High-Impact Events */}
      <Card>
        <CardHeader>
          <CardTitle>Recent High-Impact Events</CardTitle>
          <CardDescription>
            Events with significant implications for AGI timeline (Tier A/B only)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {eventsData && eventsData.items && eventsData.items.length > 0 ? (
            <div className="space-y-3">
              {eventsData.items
                .filter((event: any) => ['A', 'B'].includes(event.tier))
                .slice(0, 5)
                .map((event: any) => (
                  <div key={event.id} className="border-l-4 border-blue-500 pl-4 py-2">
                    <Link
                      href={`/events/${event.id}`}
                      className="text-base font-semibold hover:text-primary transition-colors block mb-1"
                    >
                      {event.title}
                    </Link>
                    <div className="text-sm text-muted-foreground mb-2">
                      {event.summary?.substring(0, 150)}...
                    </div>
                    {event.signpost_links && event.signpost_links.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {event.signpost_links.map((link: any) => (
                          <Badge
                            key={link.signpost_code}
                            variant="outline"
                            className="text-xs"
                          >
                            {link.signpost_code}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-muted-foreground">Loading events...</p>
          )}
        </CardContent>
      </Card>

      {/* What to Watch */}
      <Card>
        <CardHeader>
          <CardTitle>📍 What to Watch</CardTitle>
          <CardDescription>
            Key signposts approaching critical thresholds in next 6 months
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-start justify-between p-3 bg-yellow-50 border border-yellow-200 rounded">
              <div>
                <div className="font-semibold">SWE-bench Verified 85%</div>
                <div className="text-sm text-muted-foreground">
                  Currently at ~70%, predicted to hit 85% by Q2 2026
                </div>
              </div>
              <Badge className="bg-yellow-100 text-yellow-800">Q2 2026</Badge>
            </div>

            <div className="flex items-start justify-between p-3 bg-yellow-50 border border-yellow-200 rounded">
              <div>
                <div className="font-semibold">10^27 FLOP Training Run</div>
                <div className="text-sm text-muted-foreground">
                  Predicted by mid-2027, infrastructure buildout accelerating
                </div>
              </div>
              <Badge className="bg-yellow-100 text-yellow-800">Mid 2027</Badge>
            </div>

            <div className="flex items-start justify-between p-3 bg-green-50 border border-green-200 rounded">
              <div>
                <div className="font-semibold">1 GW Datacenter</div>
                <div className="text-sm text-muted-foreground">
                  xAI Colossus expansion planned for Q4 2025
                </div>
              </div>
              <Badge className="bg-green-100 text-green-800">Q4 2025</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Explanation */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>About These Insights</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>
            <strong>Forecast Drift:</strong> Compares current progress to predictions from
            Aschenbrenner's "Situational Awareness," AI 2027 scenarios, and other roadmaps.
            Positive drift = ahead of schedule; negative = behind.
          </p>
          <p>
            <strong>Security Gap:</strong> Measures difference between capabilities and
            security readiness. High gaps ({'>'}30%) indicate capabilities advancing faster than
            safety measures.
          </p>
          <p>
            <strong>High-Impact Events:</strong> Tier A (peer-reviewed) and B (official lab)
            events only. C/D tier excluded to ensure reliability.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

export default function InsightsPage() {
  return (
    <Suspense fallback={<div>Loading insights...</div>}>
      <InsightsContent />
    </Suspense>
  )
}
