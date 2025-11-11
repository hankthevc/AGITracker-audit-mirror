"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ShieldCheck,
  ShieldAlert,
  Shield,
  AlertCircle
} from "lucide-react"

interface SourceCredibility {
  publisher: string
  total_articles: number
  retracted_count: number
  retraction_rate: number
  credibility_score: number
  credibility_tier: string
  last_snapshot: string
  trend: string
}

interface CredibilityData {
  sources: SourceCredibility[]
  total_sources: number
  min_volume: number
  methodology: string
  note: string
}

const TIER_COLORS = {
  A: "bg-green-100 text-green-800 border-green-200",
  B: "bg-blue-100 text-blue-800 border-blue-200",
  C: "bg-yellow-100 text-yellow-800 border-yellow-200",
  D: "bg-red-100 text-red-800 border-red-200",
}

const TIER_ICONS = {
  A: <ShieldCheck className="h-4 w-4" />,
  B: <Shield className="h-4 w-4" />,
  C: <Shield className="h-4 w-4" />,
  D: <ShieldAlert className="h-4 w-4" />,
}

const TREND_ICONS = {
  up: <TrendingUp className="h-4 w-4 text-green-600" />,
  down: <TrendingDown className="h-4 w-4 text-red-600" />,
  stable: <Minus className="h-4 w-4 text-gray-400" />,
}

function getTierDescription(tier: string): string {
  switch (tier) {
    case "A":
      return "Highly reliable (≥90% credibility, ≥20 articles)"
    case "B":
      return "Reliable (≥75% credibility, ≥10 articles)"
    case "C":
      return "Moderate (≥50% credibility, ≥5 articles)"
    case "D":
      return "Unreliable or insufficient data (<50% credibility or <5 articles)"
    default:
      return "Unknown tier"
  }
}

export default function SourcesPage() {
  const [data, setData] = useState<CredibilityData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchCredibility() {
      try {
        const res = await fetch("/api/admin/sources/credibility")
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setData(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch source credibility")
      } finally {
        setLoading(false)
      }
    }

    fetchCredibility()
  }, [])

  if (loading) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Source Credibility</h1>
          <p className="text-muted-foreground">Loading...</p>
        </div>
        <Skeleton className="h-64 w-full" />
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

  if (!data || data.sources.length === 0) {
    return (
      <div className="container mx-auto p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold">Source Credibility</h1>
          <p className="text-muted-foreground">
            Wilson score-based publisher reliability tracking
          </p>
        </div>
        <Alert>
          <AlertDescription>
            No source credibility data available yet. 
            Credibility snapshots will be created automatically once daily.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Sort sources by credibility score (descending)
  const sortedSources = [...data.sources].sort((a, b) => b.credibility_score - a.credibility_score)

  // Group by tier
  const sourcesByTier = sortedSources.reduce((acc, source) => {
    if (!acc[source.credibility_tier]) {
      acc[source.credibility_tier] = []
    }
    acc[source.credibility_tier].push(source)
    return acc
  }, {} as Record<string, SourceCredibility[]>)

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Source Credibility</h1>
        <p className="text-muted-foreground">
          Wilson score-based publisher reliability tracking
        </p>
        <p className="text-sm text-muted-foreground mt-1">
          Tracking {data.total_sources} source{data.total_sources !== 1 ? "s" : ""} with ≥{data.min_volume} articles
        </p>
      </div>

      {/* Methodology Card */}
      <Card>
        <CardHeader>
          <CardTitle>Credibility Methodology</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">{data.methodology}</p>
          <p className="text-sm text-muted-foreground">{data.note}</p>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
            {["A", "B", "C", "D"].map((tier) => (
              <div key={tier} className="flex items-start gap-2">
                <Badge className={TIER_COLORS[tier as keyof typeof TIER_COLORS]}>
                  {tier}
                </Badge>
                <div className="text-xs text-muted-foreground">
                  {getTierDescription(tier)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Sources by Tier */}
      {["A", "B", "C", "D"].map((tier) => {
        const sources = sourcesByTier[tier] || []
        if (sources.length === 0) return null

        return (
          <Card key={tier}>
            <CardHeader>
              <div className="flex items-center gap-2">
                {TIER_ICONS[tier as keyof typeof TIER_ICONS]}
                <CardTitle>Tier {tier} Sources</CardTitle>
                <Badge variant="outline">{sources.length}</Badge>
              </div>
              <CardDescription>{getTierDescription(tier)}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {sources.map((source) => (
                  <div
                    key={source.publisher}
                    className="flex items-center justify-between p-4 rounded-lg border bg-card"
                  >
                    <div className="flex-1">
                      <div className="font-medium">{source.publisher}</div>
                      <div className="text-sm text-muted-foreground mt-1">
                        {source.total_articles} article{source.total_articles !== 1 ? "s" : ""} • 
                        {" "}{source.retracted_count} retraction{source.retracted_count !== 1 ? "s" : ""} •
                        {" "}{(source.retraction_rate * 100).toFixed(1)}% retraction rate
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {source.trend && TREND_ICONS[source.trend as keyof typeof TREND_ICONS]}
                      <div className="text-right">
                        <div className="text-lg font-semibold">
                          {(source.credibility_score * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Wilson score
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )
      })}

      {/* Info Alert */}
      <Alert>
        <AlertDescription>
          <strong>About Wilson Scores:</strong> The Wilson score confidence interval provides
          a conservative estimate of source reliability that accounts for sample size uncertainty.
          Publishers with fewer articles receive lower scores to reflect statistical uncertainty.
          Scores are updated daily based on retraction rates.
        </AlertDescription>
      </Alert>
    </div>
  )
}
