import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { SafeLink } from '@/lib/SafeLink'
import { getApiBaseUrl } from '@/lib/apiBase'

const API_URL = getApiBaseUrl()

interface Signpost {
  id: number
  code: string
  name: string
  description: string
  category: string
  baseline_value: number
  target_value: number
  unit: string
  methodology_url: string | null
  current_sota_value: number | null
  current_sota_model: string | null
  measurement_source: string | null
  why_matters: string | null
  first_class: boolean
}

async function getCapabilitySignposts(): Promise<Signpost[]> {
  try {
    const response = await fetch(
      `${API_URL}/v1/signposts?category=capabilities&first_class=true`,
      { next: { revalidate: 3600 } } // Revalidate every hour
    )
    
    if (!response.ok) {
      console.error('Failed to fetch signposts:', response.statusText)
      return []
    }
    
    return response.json()
  } catch (error) {
    console.error('Error fetching signposts:', error)
    return []
  }
}

function formatPercent(value: number | null): string {
  if (value === null) return '~0%'
  return `~${Math.round(value * 100)}%`
}

function getStatus(baseline: number, target: number, current: number | null): string {
  if (current === null) return 'Not Started'
  const progress = (current - baseline) / (target - baseline)
  if (progress >= 0.9) return 'Near Complete'
  if (progress >= 0.5) return 'In Progress'
  if (progress >= 0.1) return 'Early Stage'
  return 'Not Started'
}

export default async function BenchmarksPage() {
  const signposts = await getCapabilitySignposts()
  
  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight mb-4">Benchmark Progress</h1>
        <p className="text-xl text-muted-foreground">
          Live tracking of AI performance on first-class benchmarks
        </p>
        <p className="text-sm text-muted-foreground mt-2">
          Showing {signposts.length} capability benchmarks from the database
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {signposts.map((signpost) => {
          const status = getStatus(signpost.baseline_value, signpost.target_value, signpost.current_sota_value)
          const isHLE = signpost.code.startsWith('hle_')
          
          return (
            <Card 
              key={signpost.code} 
              data-testid={isHLE ? "hle-benchmark-tile" : "benchmark-card"}
              className={isHLE ? "border-orange-200 bg-orange-50/30" : ""}
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="flex-1">{signpost.name}</CardTitle>
                  <div className="flex flex-wrap gap-2 items-start">
                    {isHLE && (
                      <Badge 
                        variant="secondary" 
                        className="bg-orange-100 text-orange-800 hover:bg-orange-200"
                        data-testid="hle-provisional-badge"
                      >
                        Monitor-Only
                      </Badge>
                    )}
                  </div>
                </div>
                <CardDescription>{signpost.description || 'No description available'}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Current SOTA</p>
                    <p className="text-2xl font-bold">
                      {signpost.current_sota_value !== null 
                        ? formatPercent(signpost.current_sota_value)
                        : formatPercent(signpost.baseline_value)}
                    </p>
                    {signpost.current_sota_model && (
                      <p className="text-xs text-muted-foreground mt-1">{signpost.current_sota_model}</p>
                    )}
                  </div>
                  <div>
                    <p className="text-muted-foreground">Target</p>
                    <p className="text-2xl font-bold">{formatPercent(signpost.target_value)}</p>
                  </div>
                </div>
                
                {signpost.why_matters && (
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3 text-xs text-blue-800">
                    <span className="font-semibold">💡 Why this matters:</span> {signpost.why_matters}
                  </div>
                )}
                
                <div className="pt-4 border-t space-y-3">
                  <div className="flex items-center justify-between">
                    <span 
                      className={`text-sm font-medium px-3 py-1 rounded-full ${
                        status === 'In Progress' || status === 'Near Complete'
                          ? 'bg-yellow-100 text-yellow-800' 
                          : status === 'Monitor-Only' || isHLE
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}
                      data-testid={isHLE ? 'hle-monitor-only' : undefined}
                    >
                      {isHLE ? 'Monitor-Only' : status}
                    </span>
                    {signpost.measurement_source && (
                      <SafeLink
                        href={signpost.measurement_source}
                        className="text-sm text-primary hover:underline"
                      >
                        View Leaderboard →
                      </SafeLink>
                    )}
                  </div>
                  
                  <div className="pt-2">
                    <Link 
                      href={`/signposts/${signpost.code}`}
                      className="text-sm font-medium text-primary hover:underline flex items-center gap-1"
                    >
                      📚 Learn more: Why this benchmark matters →
                    </Link>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle>About These Benchmarks</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-sm max-w-none">
          <p>
            These benchmark families track AI progress toward economically transformative capabilities:
          </p>
          <ul>
            <li>
              <strong>SWE-bench Verified:</strong> Tests ability to solve real software engineering tasks,
              including bug fixes and feature additions from actual GitHub PRs.
            </li>
            <li>
              <strong>OSWorld:</strong> Measures proficiency in complex computer use, from file management
              to application interaction across multiple OS environments.
            </li>
            <li>
              <strong>WebArena:</strong> Evaluates web interaction capabilities including navigation,
              form filling, and multi-step task completion on realistic websites.
            </li>
            <li>
              <strong>GPQA Diamond:</strong> Assesses scientific reasoning at PhD level across physics,
              chemistry, and biology—requiring deep domain knowledge.
            </li>
            <li>
              <strong>HLE (Humanity&apos;s Last Exam):</strong> Monitor-only. PhD-level reasoning breadth 
              benchmark with known label-quality issues in Bio/Chem subsets. Currently B-tier (Provisional) 
              evidence only. Does not affect main composite until A-tier evidence available.
            </li>
          </ul>
          <p>
            The first four benchmarks measure <em>economically relevant</em> capabilities and directly impact 
            our main progress gauges. HLE is tracked separately as a long-horizon indicator (2026-2028) and 
            remains monitor-only pending data quality improvements or peer-reviewed validation.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

