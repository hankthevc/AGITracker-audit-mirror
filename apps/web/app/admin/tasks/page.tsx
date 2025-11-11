"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  HelpCircle,
  RefreshCw
} from "lucide-react"
import { Button } from "@/components/ui/button"

interface TaskStatus {
  status: "OK" | "DEGRADED" | "ERROR" | "PENDING" | "UNKNOWN"
  last_run: string | null
  last_success: string | null
  last_error: string | null
  error_msg: string | null
  age_seconds: number | null
}

interface TaskHealthResponse {
  overall_status: string
  summary: {
    ok: number
    degraded: number
    error: number
    pending: number
    unknown: number
  }
  tasks: Record<string, TaskStatus>
  timestamp: string
}

const STATUS_ICONS = {
  OK: <CheckCircle2 className="h-5 w-5 text-green-500" />,
  DEGRADED: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
  ERROR: <XCircle className="h-5 w-5 text-red-500" />,
  PENDING: <Clock className="h-5 w-5 text-gray-400" />,
  UNKNOWN: <HelpCircle className="h-5 w-5 text-gray-300" />,
}

const STATUS_COLORS = {
  OK: "bg-green-100 text-green-800 border-green-200",
  DEGRADED: "bg-yellow-100 text-yellow-800 border-yellow-200",
  ERROR: "bg-red-100 text-red-800 border-red-200",
  PENDING: "bg-gray-100 text-gray-600 border-gray-200",
  UNKNOWN: "bg-gray-50 text-gray-500 border-gray-100",
}

function formatAge(seconds: number | null): string {
  if (seconds === null) return "Never run"
  
  if (seconds < 60) {
    return `${Math.floor(seconds)}s ago`
  } else if (seconds < 3600) {
    return `${Math.floor(seconds / 60)}m ago`
  } else if (seconds < 86400) {
    return `${Math.floor(seconds / 3600)}h ago`
  } else {
    return `${Math.floor(seconds / 86400)}d ago`
  }
}

function formatTaskName(taskName: string): string {
  // Convert snake_case to Title Case
  return taskName
    .split("_")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ")
}

function getTaskCategory(taskName: string): string {
  if (taskName.startsWith("fetch_")) return "Data Fetchers"
  if (taskName.startsWith("ingest_")) return "News Ingestion"
  if (taskName.startsWith("map_")) return "Event Mapping"
  if (taskName.startsWith("generate_")) return "Analysis"
  if (taskName === "snap_index") return "Core"
  if (taskName === "digest_weekly") return "Communication"
  if (taskName.includes("security") || taskName.includes("inputs")) return "Weekly Tasks"
  return "Other"
}

export default function TasksPage() {
  const [health, setHealth] = useState<TaskHealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  const fetchHealth = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const apiKey = localStorage.getItem("agi_tracker_api_key")
      if (!apiKey) {
        throw new Error("No API key found. Please add ADMIN_API_KEY to localStorage as 'agi_tracker_api_key'")
      }

      const res = await fetch("/api/admin/tasks/health", {
        headers: {
          "x-api-key": apiKey,
        },
      })

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error("Invalid API key")
        }
        throw new Error(`HTTP ${res.status}: ${res.statusText}`)
      }

      const data = await res.json()
      setHealth(data)
      setLastUpdate(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch task health")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !health) {
    return (
      <div className="container mx-auto p-6 space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Task Monitoring</h1>
          <p className="text-muted-foreground">Loading task health status...</p>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-10 w-16" />
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
          <AlertDescription>
            {error}
            {error.includes("API key") && (
              <div className="mt-2">
                <p className="text-sm">To use this page:</p>
                <ol className="text-sm list-decimal list-inside mt-1">
                  <li>Get your ADMIN_API_KEY from Railway env vars</li>
                  <li>Open browser console (F12)</li>
                  <li>Run: <code className="bg-black/10 px-1 rounded">localStorage.setItem('agi_tracker_api_key', 'YOUR_KEY')</code></li>
                  <li>Refresh this page</li>
                </ol>
              </div>
            )}
          </AlertDescription>
        </Alert>
        <Button onClick={fetchHealth} className="mt-4">
          Try Again
        </Button>
      </div>
    )
  }

  if (!health) {
    return null
  }

  // Group tasks by category
  const tasksByCategory = Object.entries(health.tasks).reduce((acc, [name, status]) => {
    const category = getTaskCategory(name)
    if (!acc[category]) {
      acc[category] = []
    }
    acc[category].push({ name, ...status })
    return acc
  }, {} as Record<string, Array<TaskStatus & { name: string }>>)

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Task Monitoring</h1>
          <p className="text-muted-foreground">
            Celery task health and execution status
          </p>
          {lastUpdate && (
            <p className="text-sm text-muted-foreground mt-1">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          )}
        </div>
        <Button onClick={fetchHealth} disabled={loading} size="sm">
          <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Overall Status */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Health</CardTitle>
          <CardDescription>System-wide task execution status</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {STATUS_ICONS[health.overall_status as keyof typeof STATUS_ICONS]}
              <Badge className={STATUS_COLORS[health.overall_status as keyof typeof STATUS_COLORS]}>
                {health.overall_status}
              </Badge>
            </div>
            <div className="flex gap-6 text-sm">
              <div className="flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span className="font-medium">{health.summary.ok}</span> OK
              </div>
              <div className="flex items-center gap-1">
                <AlertTriangle className="h-4 w-4 text-yellow-500" />
                <span className="font-medium">{health.summary.degraded}</span> Degraded
              </div>
              <div className="flex items-center gap-1">
                <XCircle className="h-4 w-4 text-red-500" />
                <span className="font-medium">{health.summary.error}</span> Error
              </div>
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4 text-gray-400" />
                <span className="font-medium">{health.summary.pending}</span> Pending
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tasks by Category */}
      {Object.entries(tasksByCategory)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([category, tasks]) => (
          <Card key={category}>
            <CardHeader>
              <CardTitle>{category}</CardTitle>
              <CardDescription>
                {tasks.length} task{tasks.length !== 1 ? "s" : ""}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {tasks
                  .sort((a, b) => a.name.localeCompare(b.name))
                  .map((task) => (
                    <div
                      key={task.name}
                      className="flex items-center justify-between p-4 rounded-lg border bg-card"
                    >
                      <div className="flex items-center gap-3">
                        {STATUS_ICONS[task.status]}
                        <div>
                          <div className="font-medium">{formatTaskName(task.name)}</div>
                          <div className="text-sm text-muted-foreground">
                            {task.last_run ? (
                              <>
                                Last run: {formatAge(task.age_seconds)}
                                {task.last_success && task.last_error && 
                                 task.last_error > task.last_success && (
                                  <span className="text-red-600 ml-2">
                                    (last run failed)
                                  </span>
                                )}
                              </>
                            ) : (
                              "Never executed"
                            )}
                          </div>
                          {task.error_msg && (
                            <div className="text-sm text-red-600 mt-1">
                              Error: {task.error_msg}
                            </div>
                          )}
                        </div>
                      </div>
                      <Badge className={STATUS_COLORS[task.status]}>
                        {task.status}
                      </Badge>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        ))}

      {/* Info */}
      <Alert>
        <AlertDescription>
          <strong>Status Definitions:</strong>
          <ul className="mt-2 space-y-1 text-sm">
            <li><strong>OK:</strong> Task running successfully, last run within 24 hours</li>
            <li><strong>DEGRADED:</strong> Task successful but hasn't run in 24+ hours</li>
            <li><strong>ERROR:</strong> Last execution failed</li>
            <li><strong>PENDING:</strong> Task has never been executed</li>
            <li><strong>UNKNOWN:</strong> Unable to determine task status</li>
          </ul>
        </AlertDescription>
      </Alert>
    </div>
  )
}
