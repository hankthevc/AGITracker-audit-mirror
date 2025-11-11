"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  Key, 
  Plus, 
  Trash2, 
  RefreshCw,
  Copy,
  CheckCircle2,
  TrendingUp,
  Activity
} from "lucide-react"

interface APIKey {
  id: number
  name: string
  tier: "public" | "authenticated" | "admin"
  is_active: boolean
  created_at: string
  last_used_at: string | null
  usage_count: number
  rate_limit: number | null
  notes: string | null
}

interface APIKeysResponse {
  keys: APIKey[]
  total: number
}

interface UsageStats {
  period_days: number
  active_keys: number
  total_requests: number
  top_consumers: Array<{
    name: string
    tier: string
    requests: number
    last_used: string | null
  }>
  timestamp: string
}

interface CreateKeyResponse {
  id: number
  name: string
  tier: string
  key: string
  warning: string
}

const TIER_COLORS = {
  public: "bg-gray-100 text-gray-700 border-gray-300",
  authenticated: "bg-blue-100 text-blue-700 border-blue-300",
  admin: "bg-red-100 text-red-700 border-red-300",
}

const TIER_LABELS = {
  public: "Public (60/min)",
  authenticated: "Authenticated (300/min)",
  admin: "Admin (Unlimited)",
}

export default function APIKeysPage() {
  const [keys, setKeys] = useState<APIKey[]>([])
  const [usage, setUsage] = useState<UsageStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [includeInactive, setIncludeInactive] = useState(false)
  
  // Create key dialog state
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newKeyName, setNewKeyName] = useState("")
  const [newKeyTier, setNewKeyTier] = useState<"public" | "authenticated" | "admin">("authenticated")
  const [newKeyNotes, setNewKeyNotes] = useState("")
  const [newKeyRateLimit, setNewKeyRateLimit] = useState("")
  const [creating, setCreating] = useState(false)
  const [createdKey, setCreatedKey] = useState<CreateKeyResponse | null>(null)
  const [keyCopied, setKeyCopied] = useState(false)

  const fetchKeys = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const adminApiKey = localStorage.getItem("agi_tracker_api_key")
      if (!adminApiKey) {
        throw new Error("Admin API key not found. Please set it in localStorage.")
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/v1/admin/api-keys?include_inactive=${includeInactive}`,
        {
          headers: {
            "x-api-key": adminApiKey,
          },
        }
      )

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("Invalid admin API key. Access denied.")
        }
        throw new Error(`Failed to fetch API keys: ${response.statusText}`)
      }

      const data: APIKeysResponse = await response.json()
      setKeys(data.keys)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  const fetchUsage = async () => {
    try {
      const adminApiKey = localStorage.getItem("agi_tracker_api_key")
      if (!adminApiKey) return

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/v1/admin/api-keys/usage?days=7`,
        {
          headers: {
            "x-api-key": adminApiKey,
          },
        }
      )

      if (response.ok) {
        const data: UsageStats = await response.json()
        setUsage(data)
      }
    } catch (err) {
      console.error("Failed to fetch usage stats:", err)
    }
  }

  const createKey = async () => {
    try {
      setCreating(true)
      setError(null)
      
      const adminApiKey = localStorage.getItem("agi_tracker_api_key")
      if (!adminApiKey) {
        throw new Error("Admin API key not found.")
      }

      const params = new URLSearchParams({
        name: newKeyName,
        tier: newKeyTier,
      })
      
      if (newKeyNotes) {
        params.append("notes", newKeyNotes)
      }
      
      if (newKeyRateLimit) {
        params.append("rate_limit", newKeyRateLimit)
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/v1/admin/api-keys?${params}`,
        {
          method: "POST",
          headers: {
            "x-api-key": adminApiKey,
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to create API key: ${response.statusText}`)
      }

      const data: CreateKeyResponse = await response.json()
      setCreatedKey(data)
      
      // Reset form
      setNewKeyName("")
      setNewKeyTier("authenticated")
      setNewKeyNotes("")
      setNewKeyRateLimit("")
      
      // Refresh keys list
      await fetchKeys()
      await fetchUsage()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setCreating(false)
    }
  }

  const revokeKey = async (keyId: number, keyName: string) => {
    if (!confirm(`Are you sure you want to revoke API key "${keyName}"? This action cannot be undone.`)) {
      return
    }

    try {
      const adminApiKey = localStorage.getItem("agi_tracker_api_key")
      if (!adminApiKey) {
        throw new Error("Admin API key not found.")
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/v1/admin/api-keys/${keyId}`,
        {
          method: "DELETE",
          headers: {
            "x-api-key": adminApiKey,
          },
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to revoke API key: ${response.statusText}`)
      }

      // Refresh keys list
      await fetchKeys()
      await fetchUsage()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    }
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setKeyCopied(true)
      setTimeout(() => setKeyCopied(false), 2000)
    } catch (err) {
      console.error("Failed to copy:", err)
    }
  }

  useEffect(() => {
    fetchKeys()
    fetchUsage()
  }, [includeInactive])

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "Never"
    return new Date(dateStr).toLocaleString()
  }

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">API Key Management</h1>
        <p className="text-muted-foreground">
          Create and manage API keys for authenticated access to the AGI Tracker API.
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Usage Stats Cards */}
      {usage && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Key className="h-4 w-4" />
                Active Keys
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{usage.active_keys}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Total Requests (7d)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{usage.total_requests.toLocaleString()}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Top Consumer
              </CardTitle>
            </CardHeader>
            <CardContent>
              {usage.top_consumers.length > 0 ? (
                <div className="text-lg font-semibold truncate">
                  {usage.top_consumers[0].name}
                  <div className="text-sm text-muted-foreground font-normal">
                    {usage.top_consumers[0].requests.toLocaleString()} requests
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">No usage yet</div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Actions Bar */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchKeys()
              fetchUsage()
            }}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </Button>
          
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={includeInactive}
              onChange={(e) => setIncludeInactive(e.target.checked)}
              className="rounded"
            />
            Show inactive keys
          </label>
        </div>

        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              Create API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New API Key</DialogTitle>
              <DialogDescription>
                Create a new API key for programmatic access. The key will only be shown once.
              </DialogDescription>
            </DialogHeader>
            
            {createdKey ? (
              <div className="space-y-4">
                <Alert>
                  <AlertDescription className="space-y-2">
                    <p className="font-semibold text-yellow-700">⚠️ {createdKey.warning}</p>
                    <div className="bg-gray-100 p-3 rounded font-mono text-sm break-all">
                      {createdKey.key}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(createdKey.key)}
                      className="w-full"
                    >
                      {keyCopied ? (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy to Clipboard
                        </>
                      )}
                    </Button>
                  </AlertDescription>
                </Alert>
                
                <DialogFooter>
                  <Button
                    onClick={() => {
                      setCreatedKey(null)
                      setCreateDialogOpen(false)
                    }}
                  >
                    Done
                  </Button>
                </DialogFooter>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Name *</Label>
                  <Input
                    id="name"
                    value={newKeyName}
                    onChange={(e) => setNewKeyName(e.target.value)}
                    placeholder="e.g., Production App Key"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tier">Tier *</Label>
                  <Select value={newKeyTier} onValueChange={(v: any) => setNewKeyTier(v)}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">Public (60 req/min)</SelectItem>
                      <SelectItem value="authenticated">Authenticated (300 req/min)</SelectItem>
                      <SelectItem value="admin">Admin (Unlimited)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="rate-limit">Custom Rate Limit (optional)</Label>
                  <Input
                    id="rate-limit"
                    type="number"
                    value={newKeyRateLimit}
                    onChange={(e) => setNewKeyRateLimit(e.target.value)}
                    placeholder="Leave empty to use tier default"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Notes (optional)</Label>
                  <Textarea
                    id="notes"
                    value={newKeyNotes}
                    onChange={(e) => setNewKeyNotes(e.target.value)}
                    placeholder="Purpose of this key..."
                    rows={3}
                  />
                </div>

                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setCreateDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={createKey}
                    disabled={!newKeyName || creating}
                  >
                    {creating ? "Creating..." : "Create Key"}
                  </Button>
                </DialogFooter>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>

      {/* API Keys Table */}
      <Card>
        <CardHeader>
          <CardTitle>API Keys ({keys.length})</CardTitle>
          <CardDescription>
            Manage authentication keys for API access
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : keys.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Key className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>No API keys found</p>
              <p className="text-sm">Create your first API key to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {keys.map(key => (
                <div
                  key={key.id}
                  className={`border rounded-lg p-4 ${!key.is_active ? "opacity-50" : ""}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold">{key.name}</h3>
                        <Badge className={TIER_COLORS[key.tier]}>
                          {TIER_LABELS[key.tier]}
                        </Badge>
                        {!key.is_active && (
                          <Badge variant="secondary">Revoked</Badge>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">Created</div>
                          <div>{formatDate(key.created_at)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Last Used</div>
                          <div>{formatDate(key.last_used_at)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Usage Count</div>
                          <div>{key.usage_count.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Rate Limit</div>
                          <div>{key.rate_limit ? `${key.rate_limit}/min` : "Default"}</div>
                        </div>
                      </div>
                      
                      {key.notes && (
                        <div className="mt-2 text-sm text-muted-foreground">
                          {key.notes}
                        </div>
                      )}
                    </div>
                    
                    {key.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => revokeKey(key.id, key.name)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top Consumers Card */}
      {usage && usage.top_consumers.length > 1 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Top Consumers (Last 7 Days)</CardTitle>
            <CardDescription>Keys with highest usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {usage.top_consumers.slice(0, 5).map((consumer, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <div className="font-medium">{consumer.name}</div>
                    <div className="text-sm text-muted-foreground">
                      Tier: {consumer.tier}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{consumer.requests.toLocaleString()}</div>
                    <div className="text-xs text-muted-foreground">requests</div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
