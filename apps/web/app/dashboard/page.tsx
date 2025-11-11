'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { KpiCard } from '@/components/kpi/KpiCard'
import { TimeseriesChart } from '@/components/charts/TimeseriesChart'
import { SafeLink } from '@/lib/SafeLink'
import { Badge } from '@/components/ui/badge'
import useSWR from 'swr'
import { apiClient } from '@/lib/api'
import { HomepageSnapshot } from '@/lib/types/dashboard'

export default function DashboardPage() {
  const { data, isLoading, error } = useSWR<HomepageSnapshot>(
    '/v1/dashboard/summary',
    async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/v1/dashboard/summary`)
      if (!response.ok) throw new Error('Failed to fetch dashboard')
      return response.json()
    },
    { refreshInterval: 300000 } // Refresh every 5 minutes
  )

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto space-y-8">
        <div className="animate-pulse space-y-6">
          <div className="h-24 bg-gray-200 rounded"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1,2,3].map(i => <div key={i} className="h-32 bg-gray-200 rounded"></div>)}
          </div>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto">
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive">Error Loading Dashboard</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Failed to fetch dashboard data. Please try again later.</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Hero Section - This Week in AGI Progress */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-8">
        <h1 className="text-4xl font-bold mb-4">{data.analysis.headline}</h1>
        <ul className="space-y-2 text-lg text-muted-foreground">
          {data.analysis.bullets.map((bullet, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-blue-600 mt-1">•</span>
              <span>{bullet}</span>
            </li>
          ))}
        </ul>
        {data.analysis.paragraphs.length > 0 && (
          <p className="mt-6 text-muted-foreground leading-relaxed">
            {data.analysis.paragraphs[0]}
          </p>
        )}
      </div>

      {/* KPI Cards */}
      <div>
        <h2 className="text-2xl font-bold mb-4">Key Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.kpis.map((kpi) => (
            <KpiCard key={kpi.key} kpi={kpi} />
          ))}
        </div>
      </div>

      {/* Featured Chart */}
      {data.featured.length > 0 && (
        <div>
          <h2 className="text-2xl font-bold mb-4">Activity Trends</h2>
          <Card>
            <CardHeader>
              <CardTitle>{data.featured[0].meta?.label || 'Progress Over Time'}</CardTitle>
            </CardHeader>
            <CardContent>
              <TimeseriesChart data={data.featured[0]} height={400} showBrush={true} />
            </CardContent>
          </Card>
        </div>
      )}

      {/* News Feed */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold">Recent Developments</h2>
          <a href="/events" className="text-sm text-primary hover:underline">
            View all events →
          </a>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {data.news.slice(0, 6).map((item) => (
            <Card key={item.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <CardTitle className="text-lg leading-tight line-clamp-2">
                    {item.title}
                  </CardTitle>
                  <div className="flex gap-1 flex-shrink-0">
                    {item.tags.slice(0, 2).map((tag, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div className="text-sm text-muted-foreground">
                  {item.source} • {new Date(item.published_at).toLocaleDateString()}
                </div>
              </CardHeader>
              {item.summary && (
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {item.summary}
                  </p>
                  <SafeLink 
                    href={item.url}
                    className="text-sm text-primary hover:underline mt-3 inline-block"
                  >
                    Read more →
                  </SafeLink>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}

