"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { getApiBaseUrl } from "@/lib/apiBase"

interface Claim {
  id: number
  title: string
  summary: string
  observed_at: string
  source: {
    domain: string
    credibility: string
  }
  retracted: boolean
}

export default function AdminPage() {
  const [apiKey, setApiKey] = useState("")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [claims, setClaims] = useState<Claim[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [retractReason, setRetractReason] = useState<Record<number, string>>({})
  const [retractingId, setRetractingId] = useState<number | null>(null)

  const handleLogin = async () => {
    if (!apiKey.trim()) {
      setError("Please enter an API key")
      return
    }

    setLoading(true)
    setError("")

    try {
      const apiUrl = getApiBaseUrl()
      const response = await fetch(`${apiUrl}/v1/evidence?limit=20`, {
        headers: {
          "X-API-Key": apiKey,
        },
      })

      if (!response.ok) {
        throw new Error("Invalid API key or server error")
      }

      const data = await response.json()
      setClaims(data.results || [])
      setIsAuthenticated(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed")
      setIsAuthenticated(false)
    } finally {
      setLoading(false)
    }
  }

  const handleRetract = async (claimId: number) => {
    const reason = retractReason[claimId]
    if (!reason?.trim()) {
      alert("Please provide a reason for retraction")
      return
    }

    setRetractingId(claimId)

    try {
      const apiUrl = getApiBaseUrl()
      const response = await fetch(`${apiUrl}/v1/admin/retract`, {
        method: "POST",
        headers: {
          "X-API-Key": apiKey,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          claim_id: claimId,
          reason: reason,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP error ${response.status}`)
      }

      const result = await response.json()

      // Update claim list
      setClaims(claims.map(c => 
        c.id === claimId ? { ...c, retracted: true } : c
      ))

      // Clear reason
      setRetractReason({ ...retractReason, [claimId]: "" })

      alert(`Claim ${claimId} retracted successfully`)
    } catch (err) {
      alert(`Retraction failed: ${err instanceof Error ? err.message : "Unknown error"}`)
    } finally {
      setRetractingId(null)
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-md mx-auto mt-20">
        <Card>
          <CardHeader>
            <CardTitle>Admin Access</CardTitle>
            <CardDescription>
              Enter your API key to access admin functions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">API Key</label>
              <Input
                type="password"
                placeholder="Enter admin API key"
                value={apiKey}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setApiKey(e.target.value)}
                onKeyPress={(e: React.KeyboardEvent<HTMLInputElement>) => e.key === "Enter" && handleLogin()}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Key is stored in memory only (not persisted)
              </p>
            </div>

            {error && (
              <div className="text-sm text-destructive">
                {error}
              </div>
            )}

            <Button 
              onClick={handleLogin} 
              disabled={loading}
              className="w-full"
            >
              {loading ? "Authenticating..." : "Access Admin Panel"}
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight">Admin Panel</h1>
          <p className="text-xl text-muted-foreground">Manage claims and evidence</p>
        </div>
        <Button 
          variant="outline" 
          onClick={() => {
            setIsAuthenticated(false)
            setApiKey("")
            setClaims([])
          }}
        >
          Logout
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Claims ({claims.length})</CardTitle>
          <CardDescription>
            Review and retract claims if needed. Retracted claims are excluded from /v1/feed.json.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {claims.map((claim) => (
              <div
                key={claim.id}
                className={`p-4 border rounded-lg ${
                  claim.retracted ? "bg-muted opacity-60" : ""
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <h3 className="font-semibold">{claim.title}</h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {claim.summary}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Badge variant="outline" className="text-xs">
                        ID: {claim.id}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {claim.source.domain}
                      </Badge>
                      <Badge 
                        variant={claim.source.credibility === "A" ? "default" : "secondary"}
                        className="text-xs"
                      >
                        Tier {claim.source.credibility}
                      </Badge>
                      <span className="text-xs text-muted-foreground">
                        {new Date(claim.observed_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  {claim.retracted && (
                    <Badge variant="destructive">Retracted</Badge>
                  )}
                </div>

                {!claim.retracted && (
                  <div className="mt-4 flex gap-2">
                    <Input
                      placeholder="Reason for retraction..."
                      value={retractReason[claim.id] || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        setRetractReason({ ...retractReason, [claim.id]: e.target.value })
                      }
                      className="flex-1"
                    />
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleRetract(claim.id)}
                      disabled={retractingId === claim.id}
                    >
                      {retractingId === claim.id ? "Retracting..." : "Retract"}
                    </Button>
                  </div>
                )}
              </div>
            ))}

            {claims.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No claims found
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      <Card className="bg-amber-50 border-amber-200">
        <CardHeader>
          <CardTitle className="text-amber-900">Security Notice</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-amber-800">
          <ul className="list-disc list-inside space-y-1">
            <li>API key is stored in memory only (React state)</li>
            <li>Key is never persisted to localStorage or cookies</li>
            <li>Key is sent via X-API-Key header on each request</li>
            <li>Logout clears the key from memory</li>
            <li>All retraction actions are logged in the changelog</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}

