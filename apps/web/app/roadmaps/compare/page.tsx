import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { getApiBaseUrl } from '@/lib/apiBase'

const API_URL = getApiBaseUrl()

interface Prediction {
  id: number
  roadmap_name: string
  roadmap_slug: string
  signpost_name: string
  signpost_code: string
  prediction_text: string
  predicted_date: string
  confidence_level: string
  source_page: string
  current_progress?: number
  status?: 'ahead' | 'behind' | 'on_track'
}

async function getAllPredictions(overlayEnabled: boolean) {
  try {
    // Fetch all signposts and their predictions
    const signpostsRes = await fetch(`${API_URL}/v1/signposts`, { cache: 'no-store' })
    if (!signpostsRes.ok) return []
    const signposts = await signpostsRes.json()
    
    // Fetch predictions for each signpost
    const allPredictions: Prediction[] = []
    // Optionally fetch forecast comparisons (for overlay statuses)
    let statusIndex: Record<string, 'ahead' | 'behind' | 'on_track'> = {}
    if (overlayEnabled) {
      try {
        const compareRes = await fetch(`${API_URL}/v1/roadmaps/compare`, { cache: 'no-store' })
        if (compareRes.ok) {
          const compareData = await compareRes.json()
          // Build index by key: signpost_code|roadmap_slug
          for (const sp of compareData.signposts || []) {
            for (const rc of sp.roadmap_comparisons || []) {
              const key = `${sp.signpost_code}|${rc.roadmap_slug}`
              statusIndex[key] = rc.status
            }
          }
        }
      } catch {}
    }
    for (const signpost of signposts.slice(0, 10)) { // Limit to avoid too many requests
      try {
        const predRes = await fetch(`${API_URL}/v1/signposts/by-code/${signpost.code}/predictions`, { cache: 'no-store' })
        if (predRes.ok) {
          const data = await predRes.json()
          if (data.predictions) {
            data.predictions.forEach((pred: any) => {
              const key = `${signpost.code}|${pred.roadmap_slug}`
              const status = overlayEnabled ? statusIndex[key] : undefined
              allPredictions.push({
                ...pred,
                signpost_name: signpost.name,
                signpost_code: signpost.code,
                status,
              })
            })
          }
        }
      } catch (e) {
        // Skip failed predictions
      }
    }
    
    return allPredictions
  } catch {
    return []
  }
}

function RoadmapColumn({ roadmapName, roadmapSlug, predictions }: { 
  roadmapName: string
  roadmapSlug: string
  predictions: Prediction[] 
}) {
  const roadmapPredictions = predictions.filter(p => p.roadmap_slug === roadmapSlug)
  
  // Sort by date
  const sortedPredictions = roadmapPredictions.sort((a, b) => 
    new Date(a.predicted_date).getTime() - new Date(b.predicted_date).getTime()
  )
  
  return (
    <div className="space-y-4">
      <div className="sticky top-0 bg-background z-10 pb-4">
        <h2 className="text-2xl font-bold">{roadmapName}</h2>
        <p className="text-sm text-muted-foreground">
          {sortedPredictions.length} predictions
        </p>
      </div>
      
      <div className="space-y-3">
        {sortedPredictions.map((pred, idx) => (
          <Card key={idx} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="text-sm font-semibold">
                  <Link 
                    href={`/signposts/${pred.signpost_code}`}
                    className="hover:text-primary hover:underline"
                  >
                    {pred.signpost_name}
                  </Link>
                </CardTitle>
                {pred.status && (
                  <Badge 
                    variant="outline"
                    className={
                      pred.status === 'ahead' 
                        ? 'bg-green-100 text-green-800 border-green-300' 
                        : pred.status === 'behind'
                        ? 'bg-red-100 text-red-800 border-red-300'
                        : 'bg-yellow-100 text-yellow-800 border-yellow-300'
                    }
                  >
                    {pred.status}
                  </Badge>
                )}
              </div>
              <CardDescription className="text-xs">
                {new Date(pred.predicted_date).toLocaleDateString('en-US', { 
                  month: 'short', 
                  year: 'numeric' 
                })}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-sm">{pred.prediction_text}</p>
              
              {pred.current_progress !== undefined && (
                <div className="pt-2 border-t">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Current progress</span>
                    <span className="font-semibold">{pred.current_progress}%</span>
                  </div>
                </div>
              )}
              
              <div className="flex items-center gap-2 pt-1">
                <Badge variant="secondary" className="text-xs">
                  {pred.confidence_level}
                </Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function TimelineView({ predictions }: { predictions: Prediction[] }) {
  // Group by year
  const byYear = predictions.reduce((acc, pred) => {
    const year = new Date(pred.predicted_date).getFullYear()
    if (!acc[year]) acc[year] = []
    acc[year].push(pred)
    return acc
  }, {} as Record<number, Prediction[]>)
  
  const years = Object.keys(byYear).sort()
  
  return (
    <div className="space-y-8">
      <h2 className="text-3xl font-bold">Timeline View</h2>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-border" />
        
        <div className="space-y-12">
          {years.map(year => (
            <div key={year} className="relative pl-12">
              {/* Year marker */}
              <div className="absolute left-0 top-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                {String(year).slice(2)}
              </div>
              
              <div>
                <h3 className="text-xl font-semibold mb-4">{year}</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {byYear[parseInt(year)]
                    .sort((a, b) => new Date(a.predicted_date).getTime() - new Date(b.predicted_date).getTime())
                    .map((pred, idx) => (
                      <Card key={idx} className="text-sm">
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">
                            <Link 
                              href={`/signposts/${pred.signpost_code}`}
                              className="hover:text-primary hover:underline"
                            >
                              {pred.signpost_name}
                            </Link>
                          </CardTitle>
                          <CardDescription className="text-xs">
                            {pred.roadmap_name} • {new Date(pred.predicted_date).toLocaleDateString()}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <p className="text-xs text-muted-foreground line-clamp-2">
                            {pred.prediction_text}
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function SummaryTable({ predictions }: { predictions: Prediction[] }) {
  const roadmaps = ['aschenbrenner', 'ai-2027', 'cotra']
  const roadmapNames: Record<string, string> = {
    'aschenbrenner': "Aschenbrenner's Situational Awareness",
    'ai-2027': 'AI 2027',
    'cotra': "Cotra's Biological Anchors"
  }
  
  // Calculate summary stats
  const stats = roadmaps.map(slug => {
    const preds = predictions.filter(p => p.roadmap_slug === slug)
    const withStatus = preds.filter(p => p.status)
    const ahead = withStatus.filter(p => p.status === 'ahead').length
    const behind = withStatus.filter(p => p.status === 'behind').length
    const onTrack = withStatus.filter(p => p.status === 'on_track').length
    
    return {
      slug,
      name: roadmapNames[slug] || slug,
      total: preds.length,
      ahead,
      behind,
      onTrack,
    }
  })
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Overall Progress Summary</CardTitle>
        <CardDescription>How we're tracking against each roadmap</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-3 px-4">Roadmap</th>
                <th className="text-center py-3 px-4">Total Predictions</th>
                <th className="text-center py-3 px-4">Ahead</th>
                <th className="text-center py-3 px-4">On Track</th>
                <th className="text-center py-3 px-4">Behind</th>
                <th className="text-center py-3 px-4">Overall</th>
              </tr>
            </thead>
            <tbody>
              {stats.map(stat => {
                const netStatus = stat.ahead - stat.behind
                return (
                  <tr key={stat.slug} className="border-b">
                    <td className="py-3 px-4">
                      <Link 
                        href={`/roadmaps/${stat.slug}`}
                        className="font-medium hover:text-primary hover:underline"
                      >
                        {stat.name}
                      </Link>
                    </td>
                    <td className="text-center py-3 px-4">{stat.total}</td>
                    <td className="text-center py-3 px-4">
                      <Badge className="bg-green-100 text-green-800">{stat.ahead}</Badge>
                    </td>
                    <td className="text-center py-3 px-4">
                      <Badge className="bg-yellow-100 text-yellow-800">{stat.onTrack}</Badge>
                    </td>
                    <td className="text-center py-3 px-4">
                      <Badge className="bg-red-100 text-red-800">{stat.behind}</Badge>
                    </td>
                    <td className="text-center py-3 px-4">
                      <Badge 
                        variant="outline"
                        className={
                          netStatus > 0 
                            ? 'bg-green-50 text-green-800 border-green-300' 
                            : netStatus < 0
                            ? 'bg-red-50 text-red-800 border-red-300'
                            : 'bg-gray-50'
                        }
                      >
                        {netStatus > 0 ? '↗ Ahead' : netStatus < 0 ? '↘ Behind' : '— Even'}
                      </Badge>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}

export default async function RoadmapComparePage({
  searchParams,
}: {
  searchParams: { overlay?: string }
}) {
  const overlayEnabled = searchParams?.overlay === 'events' || searchParams?.overlay === 'true'
  const predictions = await getAllPredictions(overlayEnabled)
  
  return (
    <div className="max-w-7xl mx-auto space-y-12">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Roadmap Comparison</h1>
        <p className="text-xl text-muted-foreground">
          Compare predictions from leading AGI timeline forecasts
        </p>
        <div className="mt-4 flex items-center gap-4">
          <Link
            href={overlayEnabled ? '/roadmaps/compare' : '/roadmaps/compare?overlay=events'}
            className={`inline-flex items-center gap-2 text-sm px-3 py-1.5 rounded border ${overlayEnabled ? 'bg-primary text-white border-primary' : 'bg-white hover:bg-slate-50 border-slate-300'}`}
            data-testid="events-overlay-toggle"
            title="Toggle event-status overlay on predictions"
          >
            {overlayEnabled ? 'Events Overlay: ON' : 'Events Overlay: OFF'}
          </Link>
          {overlayEnabled && (
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
                Ahead
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-yellow-500"></span>
                On Track
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-red-500"></span>
                Behind
              </span>
              <span className="flex items-center gap-1">
                <span className="inline-block w-3 h-3 rounded-full bg-gray-300"></span>
                Unobserved
              </span>
            </div>
          )}
        </div>
      </div>
      
      <SummaryTable predictions={predictions} />
      
      <div className="space-y-6">
        <div>
          <h2 className="text-3xl font-bold mb-2">Side-by-Side Comparison</h2>
          <p className="text-muted-foreground">
            View all predictions organized by roadmap
          </p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <RoadmapColumn 
            roadmapName="Aschenbrenner's Situational Awareness" 
            roadmapSlug="aschenbrenner"
            predictions={predictions}
          />
          <RoadmapColumn 
            roadmapName="AI 2027" 
            roadmapSlug="ai-2027"
            predictions={predictions}
          />
          <RoadmapColumn 
            roadmapName="Cotra's Biological Anchors" 
            roadmapSlug="cotra"
            predictions={predictions}
          />
        </div>
      </div>
      
      <TimelineView predictions={predictions} />
      
      <div className="pt-8 border-t">
        <div className="flex gap-4">
          <Link 
            href="/roadmaps/aschenbrenner" 
            className="text-primary hover:underline font-medium"
          >
            View Aschenbrenner's roadmap →
          </Link>
          <Link 
            href="/roadmaps/ai-2027" 
            className="text-primary hover:underline font-medium"
          >
            View AI 2027 roadmap →
          </Link>
          <Link 
            href="/" 
            className="text-primary hover:underline font-medium"
          >
            Back to dashboard →
          </Link>
        </div>
      </div>
    </div>
  )
}

