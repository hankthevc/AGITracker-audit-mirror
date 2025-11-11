'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getApiBaseUrl } from '@/lib/apiBase'
import { Badge } from '@/components/ui/badge'

interface HealthResponse {
  status: string
  service?: string
  version?: string
}

interface TaskStatus {
  status: string
  last_run: string | null
  last_success: string | null
  last_error: string | null
  error_msg: string | null
  age_seconds: number | null
}

interface HealthFullResponse {
  status: string
  preset_default: string
  cors_origins: string[]
  time: string
  tasks: Record<string, TaskStatus>
}

interface IndexResponse {
  as_of_date: string
  overall: number
  capabilities: number
  agents: number
  inputs: number
  security: number
  [key: string]: any
}

export default function DebugPage() {
  const [apiBase, setApiBase] = useState<string>('')
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthFull, setHealthFull] = useState<HealthFullResponse | null>(null)
  const [index, setIndex] = useState<IndexResponse | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const base = getApiBaseUrl()
    setApiBase(base)

    // Fetch all debug endpoints
    Promise.all([
      fetch(`${base}/health`)
        .then(res => res.json())
        .then(data => setHealth(data))
        .catch(err => setErrors(prev => ({ ...prev, health: err.message }))),
      
      fetch(`${base}/health/full`)
        .then(res => res.json())
        .then(data => setHealthFull(data))
        .catch(err => setErrors(prev => ({ ...prev, healthFull: err.message }))),
      
      fetch(`${base}/v1/index?preset=equal`)
        .then(res => res.json())
        .then(data => setIndex(data))
        .catch(err => setErrors(prev => ({ ...prev, index: err.message }))),
    ]).finally(() => setLoading(false))
  }, [])

  return (
    <div className="container mx-auto py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">API Connectivity Debug</h1>
        <p className="text-muted-foreground">
          Diagnostic information for troubleshooting API connection issues
        </p>
      </div>

      {/* API Base URL */}
      <Card>
        <CardHeader>
          <CardTitle>API Base URL</CardTitle>
          <CardDescription>Currently resolved API endpoint</CardDescription>
        </CardHeader>
        <CardContent>
          <code 
            className="text-lg font-mono bg-muted p-3 rounded block"
            data-testid="debug-api-base"
          >
            {apiBase || 'Loading...'}
          </code>
          <p className="text-sm text-muted-foreground mt-2">
            Resolution order:
          </p>
          <ol className="text-sm text-muted-foreground list-decimal list-inside mt-1">
            <li>NEXT_PUBLIC_API_BASE_URL environment variable</li>
            <li>(Browser) Auto-detect from window.location (port 8000 if on :3000)</li>
            <li>Fallback: http://localhost:8000</li>
          </ol>
        </CardContent>
      </Card>

      {/* /health */}
      <Card>
        <CardHeader>
          <CardTitle>GET /health</CardTitle>
          <CardDescription>Basic health check</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : errors.health ? (
            <div className="text-destructive">
              <Badge variant="destructive">Error</Badge>
              <pre className="mt-2 text-sm">{errors.health}</pre>
            </div>
          ) : (
            <pre 
              className="bg-muted p-3 rounded text-sm overflow-auto"
              data-testid="debug-health"
            >
              {JSON.stringify(health, null, 2)}
            </pre>
          )}
        </CardContent>
      </Card>

      {/* /health/full */}
      <Card>
        <CardHeader>
          <CardTitle>GET /health/full</CardTitle>
          <CardDescription>Full configuration details</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : errors.healthFull ? (
            <div className="text-destructive">
              <Badge variant="destructive">Error</Badge>
              <pre className="mt-2 text-sm">{errors.healthFull}</pre>
            </div>
          ) : (
            <div>
              <pre 
                className="bg-muted p-3 rounded text-sm overflow-auto"
                data-testid="debug-health-full"
              >
                {JSON.stringify(healthFull, null, 2)}
              </pre>
              {healthFull && (
                <div className="mt-4 space-y-2">
                  <p className="text-sm">
                    <strong>Preset Default:</strong> {healthFull.preset_default}
                  </p>
                  <p className="text-sm">
                    <strong>CORS Origins:</strong>
                  </p>
                  <ul className="text-sm list-disc list-inside ml-4">
                    {healthFull.cors_origins.map((origin, i) => (
                      <li key={i}>{origin}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Task Watchdogs */}
              {healthFull?.tasks && (
                <div className="mt-6">
                  <h3 className="text-sm font-semibold mb-3">Task Watchdogs</h3>
                  <div className="space-y-2">
                    {Object.entries(healthFull.tasks).map(([name, task]) => (
                      <div key={name} className="flex items-center justify-between text-sm p-2 rounded bg-muted/50">
                        <span className="font-mono">{name}</span>
                        <div className="flex items-center gap-3">
                          <Badge 
                            variant={
                              task.status === 'OK' ? 'default' :
                              task.status === 'DEGRADED' ? 'secondary' :
                              task.status === 'ERROR' ? 'destructive' :
                              'outline'
                            }
                          >
                            {task.status}
                          </Badge>
                          {task.age_seconds !== null && (
                            <span className="text-muted-foreground text-xs">
                              {task.age_seconds < 3600 
                                ? `${Math.floor(task.age_seconds / 60)}m ago`
                                : `${Math.floor(task.age_seconds / 3600)}h ago`
                              }
                            </span>
                          )}
                          {task.error_msg && (
                            <span className="text-destructive text-xs truncate max-w-xs" title={task.error_msg}>
                              {task.error_msg}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* /v1/index */}
      <Card>
        <CardHeader>
          <CardTitle>GET /v1/index?preset=equal</CardTitle>
          <CardDescription>Sample index data (first 10 lines)</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p className="text-muted-foreground">Loading...</p>
          ) : errors.index ? (
            <div className="text-destructive">
              <Badge variant="destructive">Error</Badge>
              <pre className="mt-2 text-sm">{errors.index}</pre>
            </div>
          ) : (
            <div>
              <pre 
                className="bg-muted p-3 rounded text-sm overflow-auto max-h-60"
                data-testid="debug-index"
              >
                {JSON.stringify(index, null, 2).split('\n').slice(0, 15).join('\n')}
                {JSON.stringify(index, null, 2).split('\n').length > 15 && '\n  ...'}
              </pre>
              {index && (
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <strong>Overall:</strong> {(index.overall * 100).toFixed(1)}%
                  </div>
                  <div>
                    <strong>Capabilities:</strong> {(index.capabilities * 100).toFixed(1)}%
                  </div>
                  <div>
                    <strong>Agents:</strong> {(index.agents * 100).toFixed(1)}%
                  </div>
                  <div>
                    <strong>Inputs:</strong> {(index.inputs * 100).toFixed(1)}%
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Troubleshooting Tips */}
      <Card>
        <CardHeader>
          <CardTitle>Troubleshooting Tips</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div>
            <strong>If all endpoints show errors:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li>Ensure the API server is running: <code>cd services/etl && uvicorn app.main:app --port 8000</code></li>
              <li>Check Docker services: <code>docker ps</code> (should show postgres & redis)</li>
              <li>Verify the API URL above matches where your API is running</li>
            </ul>
          </div>
          <div>
            <strong>If CORS errors appear in browser console:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li>Check that <code>http://localhost:3000</code> is in the CORS origins above</li>
              <li>Set CORS_ORIGINS env var in API if needed</li>
            </ul>
          </div>
          <div>
            <strong>If /v1/index returns 0 for all categories:</strong>
            <ul className="list-disc list-inside ml-4 mt-1">
              <li>Run database seed: <code>make seed</code></li>
              <li>Fetch SWE-bench data: run the ETL task</li>
              <li>Recompute snapshots: <code>curl -X POST http://localhost:8000/v1/recompute</code></li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

