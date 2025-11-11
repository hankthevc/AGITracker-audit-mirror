"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  TrendingUp, 
  TrendingDown, 
  Zap, 
  Calendar,
  Target,
  AlertCircle
} from "lucide-react"

interface Surprise {
  event_id: number
  event_title: string
  event_date: string
  event_tier: string
  signpost_code: string
  signpost_name: string
  prediction_source: string
  predicted_date: string
  predicted_value: number | null
  surprise_score: number
  direction: "earlier" | "later"
  days_difference: number
  rationale: string | null
}

interface SurpriseData {
  surprises: Surprise[]
  count: number
  filters: {
    days: number
    limit: number
    min_score: number
  }
}

function getSurpriseColor(score: number): string {
  if (score >= 3) return "text-red-600"
  if (score >= 2) return "text-orange-600"
  if (score >= 1) return "text-yellow-600"
  return "text-gray-600"
}

function getSurpriseBadgeColor(score: number): string {
  if (score >= 3) return "bg-red-100 text-red-800 border-red-200"
  if (score >= 2) return "bg-orange-100 text-orange-800 border-orange-200"
  if (score >= 1) return "bg-yellow-100 text-yellow-800 border-yellow-200"
  return "bg-gray-100 text-gray-600 border-gray-200"
}

function getSurpriseLabel(score: number): string {
  if (score >= 3) return "Extremely Surprising"
  if (score >= 2) return "Highly Surprising"
  if (score >= 1) return "Moderately Surprising"
  return "Within Expected Range"
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString("en-US", { 
    month: "short", 
    day: "numeric", 
    year: "numeric" 
  })
}

export default function SurprisesPage() {
  const [data, setData] = useState<SurpriseData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSurprises() {
      try {
        const res = await fetch("/api/predictions/surprises")
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch surprises")
      } finally {
        setLoading(false)
      }
    }

    fetchSurprises()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Prediction Surprises</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-64" />
                <Skeleton className="h-4 w-32 mt-2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  if (!data || data.count === 0) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Prediction Surprises</h1>
          <p className="text-muted-foreground">
            Events that significantly deviated from expert forecasts
          </p>
        </div>
        <Alert>
          <AlertDescription>
            No surprising events found in the past {data?.filters.days || 90} days.
            This means recent developments are tracking closely with expert predictions.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Prediction Surprises</h1>
        <p className="text-muted-foreground">
          Events that significantly deviated from expert forecasts
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Showing {data.count} surprise{data.count !== 1 ? "s" : ""} from the past {data.filters.days} days
        </p>
      </div>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            How Surprise Scores Work
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Surprise scores measure how much an event's timing deviated from expert predictions,
            weighted by prediction uncertainty (confidence intervals).
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
            <div>
              <div className="font-semibold text-sm">0-1</div>
              <div className="text-xs text-muted-foreground">Within expected range</div>
            </div>
            <div>
              <div className="font-semibold text-sm text-yellow-600">1-2</div>
              <div className="text-xs text-muted-foreground">Moderately surprising</div>
            </div>
            <div>
              <div className="font-semibold text-sm text-orange-600">2-3</div>
              <div className="text-xs text-muted-foreground">Highly surprising</div>
            </div>
            <div>
              <div className="font-semibold text-sm text-red-600">3+</div>
              <div className="text-xs text-muted-foreground">Extremely surprising</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Surprises List */}
      <div className="space-y-4">
        {data.surprises.map((surprise) => (
          <Card key={`${surprise.event_id}-${surprise.prediction_source}`}>
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <CardTitle className="text-lg">{surprise.event_title}</CardTitle>
                  <CardDescription className="mt-1">
                    {surprise.signpost_name}
                  </CardDescription>
                </div>
                <Badge className={getSurpriseBadgeColor(surprise.surprise_score)}>
                  {getSurpriseLabel(surprise.surprise_score)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Timeline Comparison */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/30 rounded-lg">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Target className="h-4 w-4" />
                      Predicted
                    </div>
                    <div className="font-semibold">{formatDate(surprise.predicted_date)}</div>
                    <div className="text-xs text-muted-foreground">
                      by {surprise.prediction_source}
                    </div>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      Actual
                    </div>
                    <div className="font-semibold">{formatDate(surprise.event_date)}</div>
                    <div className="flex items-center gap-1 text-xs">
                      <Badge variant="outline" className="text-xs">
                        {surprise.event_tier}-tier
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      {surprise.direction === "earlier" ? (
                        <>
                          <TrendingUp className="h-4 w-4 text-green-600" />
                          Earlier than expected
                        </>
                      ) : (
                        <>
                          <TrendingDown className="h-4 w-4 text-blue-600" />
                          Later than expected
                        </>
                      )}
                    </div>
                    <div className={`font-semibold ${getSurpriseColor(surprise.surprise_score)}`}>
                      {surprise.days_difference} days
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Surprise: {surprise.surprise_score}σ
                    </div>
                  </div>
                </div>

                {/* Rationale */}
                {surprise.rationale && (
                  <div className="text-sm text-muted-foreground">
                    <strong>Prediction rationale:</strong> {surprise.rationale}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Note */}
      <Alert>
        <AlertDescription>
          <strong>Note:</strong> Surprise scores help identify areas where AGI progress is
          moving faster or slower than anticipated by expert forecasters. Events that occur
          earlier than predicted may indicate accelerating capability gains, while later events
          suggest more gradual progress.
        </AlertDescription>
      </Alert>
    </div>
  )
}
